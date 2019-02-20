# Arkham extension for pibot
### PREAMBLE ##################################################################
import copy
import re

import discord
import requests
from discord.ext import commands
from unidecode import unidecode

class Arkham:
    """Arkham Horror related commands"""

    def __init__(self, bot):
        self.bot = bot
        self.ah_api = [{}]
        self.ah_api_p = [{}]
        self.ah_api_faq = [{}]
        self.init_api = False
        self.type_code_sort = {'investigator': 0, 'asset': 1, 'event': 2, 'skill': 3, 'scenario': 4, 'treachery': 5,
                               'enemy': 6}
        self.query_corrections = {"mississippi manatee": "leo de luca",
"manatee": "leo de luca",
"ordineu": "scavenging",
"mylan": "milan",
"that same corpse again": "rotting remains",
"mr. pawterson": "cherished keepsake",
"bill": "william yorick",
"sean": "abandoned and alone",
"thud": "stunning blow",
"old sparky": "lightning gun",
"bmoc": "peter sylvestre",
"quiche": "emergency cache",
"the stranger": "the man in the pallid mask",
"pills": "painkillers",
"opium": "smoking pipe",
"dttf": "drawn to the flame",
"doot": "jim's trumpet",
"free xp": "delve too deep",
"this is fine": "deny existence",
":rat: lead": "eat lead",
"mcdog3": "guard dog",
"nick": "shotgun",
"useless": "springfield",
"god": "wendy adams",
"brandon": "preston fairmont",
"dapper as fuck": "preston",
"ian": "maniac",
"sean's waifu": "diana stanley",
"baby eaters": "drawn to the flame",
"who do you work for": "interrogate"
            }

    def refresh_ah_api(self):
        self.ah_api = sorted([c for c in requests.get('https://arkhamdb.com/api/public/cards?encounter=1').json()],
                             key=lambda card: card['name'])

        # only player cards
        self.ah_api_p = [c for c in self.ah_api if "spoiler" not in c]
        self.init_api = True

    def sort_cards(self, cards):
        # input should be a list of full card dictionaries to be sorted
        # first sort by title
        cards = sorted(cards, key=lambda card: card['name'])
        # next sort by type
        cards = sorted(cards, key=lambda card: self.type_code_sort[card['type_code']])
        return cards

    def deck_parse(self, deck_id):
        """Returns a formatted string of the cards in the given deck_id"""
        if not self.init_api:
            self.refresh_ah_api()

        api_prefix = 'https://arkhamdb.com/api/public/decklist/'
        m_response = ''
        deck_json = requests.get(api_prefix + deck_id).json()
        slots = deck_json['slots']
        slots[deck_json['investigator_code']] = "1"
        codes_to_find = slots.keys()
        decklist_data = []
        # Find every card listed in slots
        for card in self.ah_api:
            code = card["code"]
            if code in codes_to_find:
                # Save the number of copies this card in the deck_parse
                to_save = copy.copy(card)
                to_save["number"] = slots[code]
                decklist_data.append(to_save)

        # Print out a formatted list
        last_type_seen = 'investigator'
        decklist_data = self.sort_cards(decklist_data)
        m_response += "**{0}**\n".format(deck_json['name'])
        for card in decklist_data:
            if last_type_seen != card['type_code']:
                last_type_seen = card['type_code']
                m_response += "**{0}**\n".format(card['type_code'])
            xp = 0
            if "xp" in card:
                xp = int(card['xp'])
            m_response += "{0}x{1} {2}\n".format(card['number'], card['name'], "°" * (xp * int(card["number"])))

        return m_response

    @commands.command(aliases=['arkhamhelp'])
    async def ahhelp(self):
        m_response = "Hi! I'm your discord's Arkham bot. Here's what I can do:\n"
        m_response += "!ah [name] - Player card search\n"
        m_response += "!ahe [name] - Encounter card search\n"
        m_response += "!ahb [name] - Search for card backsides\n"
        m_response += "!ahX [name] - Player card search with level X\n"
        m_response += "!aha [name] - Search through all cards and post up to 5\n"
        m_response += "All !ah commands also allow a [name]~[subname] format, for cards where two or more options exist\n"
        m_response += "!ahfaq, !ahefaq, and !ahfaqX will get you the faq for the corresponding card\n"
        m_response += "!namelist - list all the current card nicknames\n"
        m_response += "!name [nickname]:[actual name] - add a card nickname.\n Note that there should be no spaces between the nickname, colon, and actual name\n"
        m_response += "!deletename [name] - remove the nickname you've listed, if it exists."

        await self.bot.say(m_response[:2000])

    @commands.command(aliases=['ahd'])
    async def ahdeck(self, *, decklist: str):
        """Arkham Horror deck listing"""
        m_decklist = unidecode(decklist.lower())
        re_decklist_id = re.search(r"(https://arkhamdb\.com/decklist/view/)(\d+)(/.*)", m_decklist)
        m_response = ""
        if re_decklist_id is None or re_decklist_id.group(2) is None:
            m_response += "I see: \"{0}\", but I don't understand\n".format(m_decklist)
        else:
            m_response += self.deck_parse(re_decklist_id.group(2))
        await self.bot.say(m_response[:2000])

    @commands.command(aliases=['listnames', 'ln'])
    async def namelist(self):

        m_response = ""

        for keys in self.query_corrections.keys():
            m_response += keys + ':' + self.query_corrections[keys] +"\n"
        await self.bot.say(m_response[:2000])



    @commands.command(aliases=['nickname','nick','rename'])
    async def name(self,*args):
        """Arkham Horror card nicknaming"""
        m_response = ""
        nickname = ' '.join(args).lower()
        if nickname.find(":") == -1:
            m_response += "Sorry, but I don't understand. Please form your nickname command as (nickname):(card name)"
        else:
            m_key,m_name = nickname.split(":", 1)
            m_cards = [c for c in self.ah_api_p if c['name'].lower().__contains__(m_key)]
            if m_cards:
                m_response += "That's already a card name. I won't be made to do evil again!"
            else:
                m_response += m_key + " now means "
                m_response += m_name
                self.query_corrections.update({m_key:m_name})

        await self.bot.say(m_response[:2000])

    @commands.command(aliases=['remove', 'cut', 'noname'])
    async def deletename(self, *args):
        m_response = ""
        ctx = ' '.join(args)


        if ctx in self.query_corrections.keys():
            del self.query_corrections[ctx]
            m_response += "key " + ctx + " deleted"
        else:
            m_response += "key " + ctx + " not found. Are you sure you had the exact name?"

        await self.bot.say(m_response[:2000])



    @commands.command(aliases=['arkham', 'arkhamhorror', 'ahe', 'ahb', 'ah1', 'ah2', 'ah3', 'ah4', 'ah5', 'aha', 'ahfaq', 'ahefaq', 'ahfaq1', 'ahfaq2', 'ahfaq3', 'ahfaq4', 'ahfaq5'], pass_context=True)
    async def ah(self, ctx):
        """Arkham Horror card lookup"""
        subexists = False
        m_query = ' '.join(ctx.message.content.split()[1:]).lower()
        img = 'imagesrc'
        faq = False
        # Auto-correct some card names (and inside jokes)
        if m_query in self.query_corrections.keys():
            m_query = self.query_corrections[m_query]

        # Auto-link some images instead of other users' names
        query_redirects = {
            }
        if m_query.find("~") >= 0:
            m_query,m_subquery = m_query.split("~",1)
            subexists = True
        m_response = ""
        if m_query in query_redirects.keys():
            m_response = query_redirects[m_query]
        elif not m_query:
            # post help text if no query
            m_response = "!ah [name] - Player card search\n"
            m_response += "!ahe [name] - Encounter card search\n"
            m_response += "!ahb [name] - Search for card backsides\n"
            m_response += "!ahX [name] - Player card search with level X\n"
            m_response += "!aha [name] - Search through all cards and post up to 5\n"
            m_response += "!ahfaq [name] - Search through all cards and post the FAQ\n"
            m_response += "All !ah commands also allow a [name]~[subname] format, for cards where two or more options exist\n"
            m_response += "!ahfaq, !ahefaq, and !ahfaqX will get you the faq for the corresponding card\n"
        else:
            # Otherwise find and handle card names
            if not self.init_api:
                self.refresh_ah_api()

            if ctx.invoked_with.__contains__("ahe"):
                # search encounter cards
                m_cards = [c for c in self.ah_api if c['name'].lower().__contains__(m_query) and "spoiler" in c]
                if not m_cards:
                    # search back side names of agendas/ acts
                    m_cards = [c for c in self.ah_api if
                               "back_name" in c and c["back_name"].lower().__contains__(m_query)]
                    img = 'backimagesrc'
            elif ctx.invoked_with[-1] in ["0", "1", "2", "3", "4", "5"]:
                # search for player cards with specific level
                n = int(ctx.invoked_with[-1])
                m_cards = [c for c in self.ah_api_p if c['name'].lower().__contains__(m_query) and c['xp'] == n]
            elif ctx.invoked_with == "ahb":
                # search card back sides
                m_cards = [c for c in self.ah_api if
                           (c['name'].lower().__contains__(m_query) and 'backimagesrc' in c) or (
                           "back_name" in c and c["back_name"].lower().__contains__(m_query))]
                img = 'backimagesrc'
            elif ctx.invoked_with == "aha":
                # search all cards
                m_cards = [c for c in self.ah_api if c['name'].lower().__contains__(m_query)]
            else:
                # search player cards
                m_cards = [c for c in self.ah_api_p if c['name'].lower().__contains__(m_query)]

            if subexists:
                m_check = [c for c in m_cards if c['subname'].lower().__contains__(m_subquery)]
                if m_check:
                    m_cards = m_check
            for c in m_cards:
                if m_query == c['name'].lower():
                    # if exact name match, post only the one card
                    m_cards = [c]
                    break
            if len(m_cards) == 1:
                try:
                    m_response += "http://arkhamdb.com" + m_cards[0][img]
                    if ctx.invoked_with.__contains__("faq"):
                        #Print it
                        holder = requests.get('http://arkhamdb.com/api/public/faq/' + m_cards[0]["code"]).json()
                        if not holder:
                            m_response = "No FAQ exists for this card. Perhaps, in another reality, it did?"
                        else:
                            m_response = holder[0]['text'];
                            m_response = re.sub("<span class=", "", m_response)
                            m_response = re.sub("icon-","",m_response)
                            m_response = re.sub("></span>", "", m_response)
                            #_response = re.sub("[\]].*?[\)]", "", m_response)
                            m_response = re.sub("[\[\]]", "", m_response)
                            #m_response = re.sub("[\<].*?[\-]","", m_response)
                            #m_response = re.sub("[\>].*?[\>]", "", m_response)
                            #m_response = re.sub("[\]].*?[\]]", "", m_response)

                            


                except KeyError as e:
                    if e.args[0] == "imagesrc":
                        # if no image on ArkhamDB
                        m_response = "'{}' has no image on ArkhamDB:\n".format(m_cards[0]['name'])
                        m_response += "https://arkhamdb.com/card/" + m_cards[0]["code"]
            elif len(m_cards) == 0:
                m_response += "Sorry, I cannot seem to find any card with these parameters:\n"
                m_response += "http://arkhamdb.com/find/?q=" + m_query.replace(" ", "+")
            else:
                if ctx.invoked_with == "aha":
                    # post up to 5 images with !aha command
                    for i, card in enumerate(m_cards[:5]):
                        m_response += "http://arkhamdb.com{0}\n".format(card[img])
                    if len(m_cards) > 5:
                        m_response += "[{0}/{1}]".format(5, len(m_cards))
                else:
                    # else just post a link
                    m_response = "'{}' matching cards found:\n".format(len(m_cards))
                    m_response += "https://arkhamdb.com/find?q=" + m_query.replace(" ", "+")
        await self.bot.say(m_response[:2000])


def setup(bot):
    bot.add_cog(Arkham(bot))
