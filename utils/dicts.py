
class Map:

    def __init__(self, keys: list, values: list[list]):
        self.mapping = []
        for t in values:
            d = dict(zip(keys, t))
            self.mapping.append(d)

    def __getitem__(self, i) -> dict:
        return self.mapping[i]

    def get(self, target) -> dict:
        for d in self.mapping:
            if target in d.values():
                return d
        raise KeyError('Target is not present in map.')

    def list(self, key) -> list:
        return [d[key] for d in self.mapping]


cmdlist = '**\*** \\spreadsheet - Get link to spreadsheet\n' \
          '**\*** \\links - Get links to helpful track breaking resources\n' \
          '**\*** \\list - Get a list of supported tracks\n' \
          '\n' \
          '**\*** \\info <track name> - Get general track information\n' \
          '**\*** \\cpinfo <track name> - Get stats for track\'s checkpoint map\n' \
          '**\*** \\vid <track name> - Get video of track\'s ultra shortcut\n' \
          '**\*** \\bkt <track name> [glitch/no-sc] [flap] [200cc] - Get specified BKT\n' \
          '**\*** \\pop [timeframe] <track name> - Get track\'s popularity ranking\n' \
          '**\*** \\random [all] - Get info on a random track\n' \
          '\n' \
          '**\*** \\img <track name> - Get image of track\'s checkpoint map\n' \
          '**\*** \\szs <track name> - Download track\'s szs file\n' \
          '**\*** \\kmp <track name> - Download track\'s kmp and kcl files\n' \
          '**\*** \\kmptext <track name> - Get track kmp in both raw and text form\n' \
          '**\*** \\kcltext <track name> - Get track kcl in both raw and text form\n' \
          '**\*** \\gcps <track name> - Generates Desmos graph of the full track.\n' \
          '\n' \
          '<track name> accepts any custom track in CTGP. Track names are case insensitive and can be replaced with ' \
          'abbreviations (\"dcr\", \"snes mc2\", etc.).'

links = 'CTGP Tockdom Page:\n' \
        'http://wiki.tockdom.com/wiki/CTGPR\n\n' \
        'CTGP Track Files Dropbox (outdated, use bot commands instead):\n' \
        'https://www.dropbox.com/sh/9phl0p4d663fmel/AAD0Xo4JyuYZng3AW4ynb2Nwa?dl=0\n\n' \
        'CTGP Upcoming Track Updates:\n' \
        'https://docs.google.com/spreadsheets/d/1xwhKoyypCWq5tCRTI69ijJoDiaoAVsvYAxz-q4UBNqM/edit?usp=sharing\n\n' \
        'Download Lorenzi\'s KMP Editor:\n' \
        'https://github.com/hlorenzi/kmp-editor/releases\n\n' \
        'Download CTools:\n' \
        'http://www.chadsoft.co.uk/ctools/setup/ctoolssetup.msi\n\n' \
        'Download SZS Modifier (requires .NET 2.0):\n' \
        'http://www.chadsoft.co.uk/wiicoder/SZSModifierSetup.zip'

gcat = {
    'Yes': 'Unbreakable (Last CP is KCP)',
    'Yes*': 'Unbreakable (95% Rule)',
    'Yes**': 'Unbreakable (Last KCP isn\'t loaded)',
    'Not Glitched': 'Not Glitched',
    'Glitched': '150cc RTA',
    '200cc Only': '200cc RTA',
    'Flap Only': '150cc Flap RTA',
    '200cc Flap': '200cc Flap RTA',
    'Slower than NG': '150cc RTA (Slower than No Glitch)',
    '200cc Slower': '200cc RTA (Slower than No Glitch)',
    'NLC Glitch': '150cc No Lap Count Glitch',
    '200cc NLC': '200cc No Lap Count Glitch',
    'Lap 4 Bug': 'Lap 4 Bug',
    'TASed': '150cc TASed',
    '150cc TASed': '150cc TASed',
    'TASed Faster than NG': '150cc TASed (Faster than No Glitch)',
    '200cc TASed': '200cc TASed',
    'Flap TASed': '150cc Flap TASed',
    '150cc Flap TASed': '150cc Flap TASed',
    '200cc Flap TASed': '200cc Flap TASed',
    'Impossible': 'Impossible',
    'TASed on older version': 'TASed on Older Version'
}

prefixes = ['SNES', 'GBA', 'N64', 'GCN', 'DS', 'CTR', 'DKR', 'GP', 'SADX']

lbcat = [
    '150cc',
    '150cc Glitch',
    '150cc No SC',
    '',
    '200cc',
    '200cc Glitch',
    '200cc No SC'
]

popcat = Map(['name', 'id', 'desc'], [
    ['M1', 0, 'Current month (M1)'],
    ['M3', 1, 'Within last 3 months (M3)'],
    ['M6', 2, 'Within last 6 months (M6)'],
    ['M9', 3, 'Within last 9 months (M9)'],
    ['M12', 4, 'Within last 12 months (M12)']
])

vehicle_id = [
    'Standard Kart S',
    'Standard Kart M',
    'Standard Kart L',
    'Booster Seat',
    'Classic Dragster',
    'Offroader',
    'Mini Beast',
    'Wild Wing',
    'Flame Flyer',
    'Cheep Charger',
    'Super Blooper',
    'Piranha Prowler',
    'Tiny Titan',
    'Daytripper',
    'Jetsetter',
    'Blue Falcon',
    'Sprinter',
    'Honeycoupe',
    'Standard Bike S',
    'Standard Bike M',
    'Standard Bike L',
    'Bullet Bike',
    'Mach Bike',
    'Flame Runner',
    'Bit Bike',
    'Sugarscoot',
    'Wario Bike',
    'Quacker',
    'Zip Zip',
    'Shooting Star',
    'Magikruiser',
    'Sneakster',
    'Spear',
    'Jet Bubble',
    'Dolphin Dasher',
    'Phantom'
]

driver_id = [
    'Mario',
    'Baby Peach',
    'Waluigi',
    'Bowser',
    'Baby Daisy',
    'Dry Bones',
    'Baby Mario',
    'Luigi',
    'Toad',
    'Donkey Kong',
    'Yoshi',
    'Wario',
    'Baby Luigi',
    'Toadette',
    'Koopa Troopa',
    'Daisy',
    'Peach',
    'Birdo',
    'Diddy Kong',
    'King Boo',
    'Bowser Jr.',
    'Dry Bowser',
    'Funky Kong',
    'Rosalina',
    'Small Mii Outfit A (Male),',
    'Small Mii Outfit A (Female),',
    'Small Mii Outfit B (Male),',
    'Small Mii Outfit B (Female),',
    'Small Mii Outfit C (Male),',
    'Small Mii Outfit C (Female),',
    'Medium Mii Outfit A (Male),',
    'Medium Mii Outfit A (Female),',
    'Medium Mii Outfit B (Male),',
    'Medium Mii Outfit B (Female),',
    'Medium Mii Outfit C (Male),',
    'Medium Mii Outfit C (Female),',
    'Large Mii Outfit A (Male),',
    'Large Mii Outfit A (Female),',
    'Large Mii Outfit B (Male),',
    'Large Mii Outfit B (Female),',
    'Large Mii Outfit C (Male),',
    'Large Mii Outfit C (Female),',
    'Medium Mii',
    'Small Mii',
    'Large Mii',
    'Peach',
    'Daisy',
    'Rosalina',
]

controller_id = [
    'Wii Wheel',
    'Wiimote & Nunchuk',
    'Classic',
    'Gamecube'
]

regs = Map(['name', 'alias', 'slot', 'sha1'], [
    ['Luigi Circuit', 'LC', '08', '1AE1A7D894960B38E09E7494373378D87305A163'],
    ['Moo Moo Meadows', 'MMM', '01', '90720A7D57A7C76E2347782F6BDE5D22342FB7DD'],
    ['Mushroom Gorge', 'MG', '02', '0E380357AFFCFD8722329994885699D9927F8276'],
    ['Toad\'s Factory', 'TF', '04', '1896AEA49617A571C66FF778D8F2ABBE9E5D7479'],
    ['Mario Circuit', 'MC', '00', '7752BB51EDBC4A95377C0A05B0E0DA1503786625'],
    ['Coconut Mall', 'CM', '05', 'E4BF364CB0C5899907585D731621CA930A4EF85C'],
    ['DK Summit', 'DKSC', '06', 'B02ED72E00B400647BDA6845BE387C47D251F9D1'],
    ['Wario\'s Gold Mine', 'WGM', '07', 'D1A453B43D6920A78565E65A4597E353B177ABD0'],
    ['Daisy Circuit', 'DC', '09', '72D0241C75BE4A5EBD242B9D8D89B1D6FD56BE8F'],
    ['Koopa Cape', 'KC', '0F', '52F01AE3AED1E0FA4C7459A648494863E83A548C'],
    ['Maple Treeway', 'MT', '0B', '48EBD9D64413C2B98D2B92E5EFC9B15ECD76FEE6'],
    ['Grumble Volcano', 'GV', '03', 'ACC0883AE0CE7879C6EFBA20CFE5B5909BF7841B'],
    ['Dry Dry Ruins', 'DDR', '0E', '38486C4F706395772BD988C1AC5FA30D27CAE098'],
    ['Moonview Highway', 'MH', '0A', 'B13C515475D7DA207DFD5BADD886986147B906FF'],
    ['Bowser\'s Castle', 'BC', '0C', 'B9821B14A89381F9C015669353CB24D7DB1BB25D'],
    ['Rainbow Road', 'RR', '0D', 'FFE518915E5FAAA889057C8A3D3E439868574508'],
    ['GCN Peach Beach', 'rPB', '10', '8014488A60F4428EEF52D01F8C5861CA9565E1CA'],
    ['DS Yoshi Falls', 'rYF', '14', '8C854B087417A92425110CC71E23C944D6997806'],
    ['SNES Ghost Valley 2', 'rGV2', '19', '071D697C4DDB66D3B210F36C7BF878502E79845B'],
    ['N64 Mario Raceway', 'rMR', '1A', '49514E8F74FEA50E77273C0297086D67E58123E8'],
    ['N64 Sherbet Land', 'rSL', '1B', 'BA9BCFB3731A6CB17DBA219A8D37EA4D52332256'],
    ['GBA Shy Guy Beach', 'rSGB', '1F', 'E8ED31605CC7D6660691998F024EED6BA8B4A33F'],
    ['DS Delfino Square', 'rDS', '17', 'BC038E163D21D9A1181B60CF90B4D03EFAD9E0C5'],
    ['GCN Waluigi Stadium', 'rWS', '12', '418099824AF6BF1CD7F8BB44F61E3A9CC3007DAE'],
    ['DS Desert Hills', 'rDH', '15', '4EC538065FDC8ACF49674300CBDEC5B80CC05A0D'],
    ['GBA Bowser Castle 3', 'rBC3', '1E', 'A4BEA41BE83D816F793F3FAD97D268F71AD99BF9'],
    ['N64 DK\'s Jungle Parkway', 'rDKJP', '1D', '692D566B05434D8C66A55BDFF486698E0FC96095'],
    ['GCN Mario Circuit', 'rMC', '11', '1941A29AD2E7B7BBA8A29E6440C95EF5CF76B01D'],
    ['SNES Mario Circuit 3', 'rMC3', '18', '077111B996E5C4F47D20EC29C2938504B53A8E76'],
    ['DS Peach Gardens', 'rPG', '16', 'F9A62BEF04CC8F499633E4023ACC7675A92771F0'],
    ['GCN DK Mountain', 'rDKM', '13', 'B036864CF0016BE0581449EF29FB52B2E58D78A4'],
    ['N64 Bowser\'s Castle', 'rBC', '1C', '15B303B288F4707E5D0AF28367C8CE51CDEAB490'],
])

aliases = {
    'ASDF': 'ASDF_Course',
    'DKSC': 'DK Summit',
    'DK\'S SNOWBOARD CROSS': 'DK Summit'
}
for r in regs:
    aliases[r['alias'].upper()] = r['name']

cleaned = [
    'Castle Of Time',
    'Dawn Township',
    'Headlong Skyway',
    'Incendia Castle',
    'Mushroom Peaks',
    'Six King Labyrinth',
    'Sunset Ridge'
]
