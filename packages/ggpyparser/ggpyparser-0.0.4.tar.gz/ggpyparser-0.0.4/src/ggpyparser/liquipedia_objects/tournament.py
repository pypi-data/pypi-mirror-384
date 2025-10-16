"""
Module for representing and extracting information about a tournament.

Defines the Tournament class, provides
methods to fetch and parse tournament data like the prize pool

Classes
-------
Tournament
    Represents an individual tournament and provides methods to extract structured information
    about the competition

Dependencies
------------
- BeautifulSoup
- pandas
- re
- mwparserfromhell: For parsing MediaWiki markup.
- parse_liquipedia, parse_liquipedia_html, Custom modules for parsing specific data blocks.
- LiquipediaPage: Base class for interacting with Liquipedia.

"""
from typing import List, Union
from collections import defaultdict
import warnings
import re
import mwparserfromhell as mw
import pandas as pd

from bs4 import BeautifulSoup
from bs4.element import Tag
from ggpyparser.parse_liquipedia import parse_liquipedia_html, parse_liquipedia_wc
from ggpyparser.liquipedia_objects import liquipedia_page
class Tournament(liquipedia_page.LiquipediaPage):
    """
    A class to represent a tournament


    Methods
    -------
    get_info(infobox_name = "Infobox team")
        Parses information from tournament's infobox
    get_results()
        Get tournament results
    get_participants()
        Get all participants
    get_talent()
        Get all talent
    get_prizes()
        Get the tournament's prize pool
    """
    def __init__(self, game : str, name : str,
                 user : str,  action : str = "wikicode"
                 ) -> None:
        """
        Creates a tournament object

        Parameters
        ----------
        game: str
            The game being played
        name: str
            The page name, found by liquipedia.com/game/(name)
        user: str
            The user, as requested by liquipedia ToS
        action: str
            Whether html(action = "parse") or wikicode(action = "wikicode") parsing should occur
        """
        super().__init__(game, name, user=user, action = action)

    def _get_matches_wc(self) -> pd.DataFrame:
        """A private function to parse matches with wikicode"""
        sections = []
        parses = []
        str_parsed = mw.parse(self.raw_str)
        headings = [heading.title.strip().lower()  for heading in str_parsed.filter_headings()]
        results_sections = ['results', "result"] if "results" in headings else ["group stage",
                                                                      "playoffs", "main event"]
        for section in str_parsed.get_sections(include_lead=True, include_headings=True):
            if len(section.filter_headings()) == 0:
                continue
            #exists probably a cleaner solution to find relevant headers
            heading = section.filter_headings()[0].title.strip().lower()
            #find all results sections
            if heading in results_sections:
                #results = section.get_sections(include_lead=False, include_headings=False)
                parse = mw.parse(section)
                parses.append(parse) #incase of multiple "results" sections
        games_df = []
        #for all the results sections
        for parse in parses:
            sections = parse.get_sections(include_lead=False, include_headings=True)
            # Handle single-section tournaments (no subsections)
            if not sections:
                stage = "playoffs" if "Bracket" in parse else "group_stage"
                new_games = parse_liquipedia_wc.parse_games(stage, parse)
                new_games['stage_group'] = stage
                games_df.append(new_games)
                continue
            seen_stages = []
            lowest_sections = parse_liquipedia_wc.get_lowest_subsections(parse)
            for lowest in lowest_sections:
                stage = lowest.filter_headings()[0].title.strip().lower()
                if str(lowest) in seen_stages or "{{Match" not in str(lowest):
                    continue
                seen_stages.append(str(lowest))
                match = re.search(r"\{\{[^|]+\|([^}]+)\}\}", stage, re.I)
                if match:
                    stage = match.group(1).strip().lower()
                for low in lowest.split("{{Stage|"):
                    if "{{Match" not in low:
                        continue
                    new_games = parse_liquipedia_wc.parse_games(stage, low)
                    new_games['stage_group'] = stage
                    games_df.append(new_games)
        matches = pd.concat(games_df, ignore_index=True)
        if len(parses) > 0 and len(matches) == 0:
            raise parse_liquipedia_wc.SectionNotFoundException(
            "Found results section but could not parse game data, it is likely" \
            " that the game data is not in the wikicode for this tournament")
        if len(games_df) == 0:
            raise parse_liquipedia_wc.SectionNotFoundException(
            "Could not find the results section on the page, " \
            "ensure that the page has a results" \
            " section. If this tournament has stages, " \
            "it is likely that the results section is in the stage pages")
        return matches

    def _get_matches_html(self) -> pd.DataFrame:
        """A private function to parse matches with html"""
        match_idx = 0
        souped = BeautifulSoup(self.get_raw_str(), "html.parser")
        matchlists = souped.select(
        "div.general-collapsible.brkts-matchlist"
        )
        all_matches = []
        for matchlist in matchlists:
            header = matchlist.find_previous(["h1", "h2", "h3", "h4", "h5", "h6"])
            header = header.get_text().split("[")[0] if header else None
            title = matchlist.select(
                "div.brkts-matchlist-title")[0].get_text().replace(" Show Hide", "")
            matches = matchlist.find_all("div", class_ = "brkts-popup brkts-match-info-popup")
            for match in matches:
                parsed = parse_liquipedia_html.parse_match_html(match)
                parsed['stage'] = header
                parsed['substage'] = title
                parsed['match_idx'] = match_idx
                match_idx += 1
                all_matches.append(parsed)
        #parse brackets
        brackets = souped.select('div[class="brkts-bracket"]')
        for b_round in brackets:
            header = b_round.find_previous(["h1", "h2", "h3", "h4", "h5", "h6"])
            header = header.get_text().split("[")[0] if header else None
            subround_names = b_round.select('div[class="brkts-header brkts-header-div"]')
            subbrackets = b_round.find_all("div", class_="brkts-round-body", recursive = False)
            for subbracket in subbrackets:
                closest_header = subbracket.find_previous("div", class_="brkts-round-header")
                subround_names = [subround_name.contents[0]
                                  for subround_name in closest_header]
                subround_names = [name for name in subround_names
                                  if str(name).lower().strip() != "qualified"]
                output = parse_liquipedia_html.parse_bracket_recursive_html(
                    subbracket, subround_names)
                for sub_round, body in output.items():
                    for match in body:
                        parsed = parse_liquipedia_html.parse_match_html(match)
                        parsed['stage'] = header
                        parsed['substage'] = sub_round
                        parsed['match_idx'] = match_idx
                        match_idx += 1
                        all_matches.append(parsed)
        #get single matches(mostly showmatches or
        #grand-finals where the finalists are weirdly determined)
        single_matches = souped.find_all(
            "div", class_ = "brkts-popup brkts-popup brkts-match-info-flat")
        for match in single_matches:
            header = match.find_previous("span", class_="mw-headline").get_text()
            parsed = parse_liquipedia_html.parse_match_html(match)
            parsed['stage'] = header
            parsed['substage'] = header
            all_matches.append(parsed)
        if len(all_matches) == 0:
            raise parse_liquipedia_wc.SectionNotFoundException("No matches found")
        all_matches = pd.concat(all_matches)
        if all_matches.shape[0] == 0:
            warnings.warn("Found a Matches Section but no actual match data was found. " \
            "If this tournament has not started yet this is expected.")
            #TODO: for tournaments yet to be played, still return structure of tournament
        return all_matches.reset_index(drop = True)

    def get_results(self) -> pd.DataFrame:
        """Gets the results of a tournament"""
        if self.action == "wikicode":
            return self._get_matches_wc()
        return self._get_matches_html()

    def get_participants(self) -> pd.DataFrame:
        """Gets the participants of a tournament"""
        if self.action == "wikicode":
            return self._get_participants_wc()
        return self._get_participants_html()

    def _get_participants_html(self) -> pd.DataFrame:
        """Private function to get participants with html parsing"""
        raw_str = BeautifulSoup(self.get_raw_str(), "html.parser")
        participants = []
        for team in raw_str.find_all("div", class_ = "teamcard toggle-area toggle-area-1"):
            team_dict = {}
            header = team.find_previous(["h1", "h2", "h3", "h4", "h5", "h6"])
            header = header.get_text().split("[")[0] if header else None
            team_dict['name'] = team.find("center").get_text() if team.find("center") else None
            nums = team.find("table",
                            class_ =  "wikitable wikitable-bordered list active").find_all("tr")
            team_dict['qualification'] = (qual := team.find("td",
                                        class_="teamcard-qualifier")) and qual.get_text()
            team_dict['stage_enter'] = header

            for num in nums:
                text = str(num.get_text()).split()
                team_dict[f"p{text[0]}"] = text[1]
            participants.append(team_dict)
        if len(participants) == 0:
            raise parse_liquipedia_wc.SectionNotFoundException(
                "Could not find participants section")
        return pd.DataFrame(participants).reset_index(drop = True)

    def _get_participants_wc(self) -> pd.DataFrame:
        """Private function to get participants with wikicode parsing"""
        str_parsed = mw.parse(self.get_raw_str())
        all_players = []
        for section in str_parsed.get_sections(matches=r"(?i)^participants$"):
            lowest_section = parse_liquipedia_wc.get_lowest_subsections(section)
            for lowest in lowest_section:
                participant_stage = lowest.filter_headings()[0].title.strip().lower()
                match_tpl = [t for t in lowest.filter_templates(recursive=True)
                        if t.name.matches("ParticipantSection") or t.name.matches('TeamCard')]
                for participant in match_tpl:
                    p_dict = {"stage": participant_stage}
                    for param in participant.params:
                        text = str(param.value)
                        matches = re.findall(r"\[\[(.*?)\]\]", text)
                        if matches:
                            text = matches[0]
                        p_dict[str(param.name)] = re.sub(r"[{}\[\]]", "", text).split("|")[-1]
                    all_players.append(p_dict)
        return pd.DataFrame(all_players)

    def get_talent(self) -> pd.DataFrame:
        """Gets the talent of a tournament"""
        if self.action == "wikicode":
            return self._get_talent_wc()
        return self._get_talent_html()

    def _get_talent_html(self) -> pd.DataFrame:
        """Private function to get participants with html parsing"""
            #no explitict talent section in html, have to scan for ids
        souped = BeautifulSoup(self.get_raw_str(), "html.parser")
        all_talent = []
        talent_section = talent_span.parent if (talent_span :=
                                souped.find("span", {"id": "Broadcast_Talent"})) else None
        #could change depending on title, look in the future
        talent_container = talent_section.find_all("div",
                                    class_="tabs-content") if talent_section else None
        template_boxes = []
        if not talent_container:
            talent_container = talent_section.find_next_sibling("div") if talent_section else None
        if isinstance(talent_container, Tag):
            template_boxes = [
                    box for box in talent_container.find_all("div", class_="template-box")
                    if not box.find("div", class_="template-box")  # deepest level check
            ] + [box for box in talent_container.find_all("ul")]
        if not template_boxes and talent_section:
            template_boxes = list(filter(None, [talent_section.find_next("ul")]))
        for role_box in template_boxes:
            role_title = role_box.find("b")
            if role_title:
                if not isinstance(role_box, Tag) or not isinstance(role_title, Tag):
                    raise parse_liquipedia_wc.SectionNotFoundException(
                        "Unable to parse role box, not a bs4 Tag")
                role_name = role_title.get_text(strip=True).rstrip(":")
                for li in role_box.find_all("li"):
                    text = li.get_text().split("\n")
                    if len(text) > 1:
                        continue
                    flag = li.find("a")
                    country = flag['title'] if flag else None
                    talent_roles = {}
                    match = re.search(r'\xa0([^\xa0(]+)\xa0\(([^)]+)\)', text[0])
                    if match:
                        talent_roles['displayname'] = match.group(1).strip()
                        talent_roles['fullname'] = match.group(2).strip()
                        talent_roles['country'] = country
                    talent_roles["role"] = role_name
                    all_talent.append(talent_roles)
        if len(all_talent) == 0:
            raise parse_liquipedia_wc.SectionNotFoundException("Could not find talent section")
        all_talent = pd.DataFrame(all_talent)
        if "fullname" in all_talent.columns:
            #band-aid fix since the talent can be sometimes be parsed multiple times
            #this usually happens with tournaments with different stages and
            # if the talent section a mix of tabs and non-tabs
            return all_talent.drop_duplicates(subset="fullname", keep='last',
                                               inplace=False).reset_index(drop = True)
        all_talent = all_talent.drop_duplicates(subset = "role", inplace = False)
        if len(all_talent.columns) == 1:
            #if not announced, manually fill with TBA
            #this might cause some side-effects tho, so look out in future
            all_talent['fullname'] = "TBA"
        return all_talent.reset_index(drop = True)




    def _get_talent_wc(self) -> pd.DataFrame:
        """Private function to get participants with wikicode parsing"""
        #TODO: add language of talent
        talent_stage = 1
        broadcast_df = []
        str_parsed = mw.parse(self.raw_str)
        for section in str_parsed.get_sections(
            matches=r"(?i)^(broadcast talent|talent)$",
            include_lead=False,
            include_headings=True
        ):
            parse = mw.parse(section)
            #TODO: change to template matching instead of regex
            pattern = r"\{\{[Bb]roadcasterCard.*?\}\}"
            roles = re.findall(pattern, str(parse), re.DOTALL)
            for role in roles:
                role_df = parse_liquipedia_wc.parse_talent(role)
                role_df['talent_stage'] = talent_stage
                broadcast_df.append(role_df)
            talent_stage += 1
        if len(broadcast_df) == 0:
            raise parse_liquipedia_wc.SectionNotFoundException(
            "Could not find talent section on the page," \
            " ensure that the page has a talent" \
            "section. If this is a stage of a larger tournament, " \
            "it is likely that the talent section is in the tournament overview")
        return pd.concat(broadcast_df).reset_index(drop = True)
        #because of ul and div mixing for talent,
        #we need to do both which leads to double counting occassionally
        #might be a fix but seems difficult without sacrificing not counting some

    def get_prizes(self) -> Union[List[pd.DataFrame], pd.DataFrame]:
        """Gets the prize pool for a tournament"""
        if self.action == "wikicode":
            return self._get_prizes_wc()
        return self._get_prizes_html()

    def _get_prizes_html(self) -> Union[List[pd.DataFrame], pd.DataFrame]:
        """Private function to get prize pool with html parsing"""
        souped = BeautifulSoup(self.get_raw_str(), "html.parser")
        prize_pools = souped.find_all("div",
                    class_ = "csstable-widget collapsed general-collapsible prizepooltable")
        df_list = []
        for prize_pool in prize_pools:
            header = prize_pool.find("div", class_ = "csstable-widget-row prizepooltable-header")
            headers = [h.get_text(strip=True).lower() for h in
                       header.select(".csstable-widget-cell")]
            rows = []

            col_map = {idx: col_name for idx, col_name in enumerate(headers)}
            prize_rows = prize_pool.select(
            "div.csstable-widget-row:not(.prizepooltable-header):not(.ppt-toggle-expand)")
            for row in prize_rows:
                row_dict = defaultdict(list)
                cells = row.select(".csstable-widget-cell")
                teams = row.find_all("div", class_ = "block-team")
                teams =  [team.get_text() for team in teams]

                current_idx = 0
                span_idx = 0
                non_spans = []
                #check for spans
                spans = [cell for cell in cells if cell.get("style") and
                          "span" in cell.get("style") and
                          int(re.search(r"span (\d+)", cell["style"]).group(1)) > 1]

                for cell in cells:
                    if len(spans) > 0 and (not cell.get("style") or "span"
                                           not in cell.get("style")) and current_idx < len(col_map):
                        non_spans.append(current_idx)
                    if current_idx >= len(col_map):
                        new_idx = non_spans[span_idx %
                                            len(non_spans)] if len(non_spans) > 0 else new_idx
                        span_idx += 1
                        colname = col_map[new_idx]
                        row_dict[colname].append(cell.get_text(strip=True))
                    #print(cell)
                    else:
                        colname = col_map[current_idx]
                        row_dict[colname].append(cell.get_text(strip=True))
                        current_idx += 1
                    #colname = col_map[idx]
                    #print(cell.get_text())
                row_dict = {k: v[0] if len(v) == 1 else v for k, v in row_dict.items()}
                rows.append(row_dict)
            df_list.append(pd.DataFrame(rows).reset_index(drop = True))
        if len(df_list) == 0:
            raise parse_liquipedia_wc.SectionNotFoundException("Could not find prizes section")
        return df_list[0] if len(df_list) == 1 else df_list

    def _get_prizes_wc(self) -> pd.DataFrame:
        """Private function to get prize pool with wikicode parsing"""
        prizes = []
        str_parsed = mw.parse(self.raw_str)
        for section in str_parsed.get_sections(matches=r"(?i)^prize pool"):
            if "prize pool start" in str(section):
                prize_df = parse_liquipedia_wc.parse_prizes(section, match_1 = "prize pool slot",
                                                            match_2 = r"(?i)prize pool start")
            else:
                prize_df = parse_liquipedia_wc.parse_prizes(section)
            prizes.append(prize_df)

        return pd.concat(prizes).reset_index(drop = True)
