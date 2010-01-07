#!/usr/bin/python
# -*- encoding: utf-8

normalization_table = {
       u"Ḅ": u"b", u"Ć": u"c", u"Ȍ": u"o", u"ẏ": u"y", u"Ḕ": u"e", u"Ė": u"e",
       u"ơ": u"o", u"Ḥ": u"h", u"Ȭ": u"o", u"ắ": u"a", u"Ḵ": u"k", u"Ķ": u"k",
       u"ế": u"e", u"Ṅ": u"n", u"ņ": u"n", u"Ë": u"e", u"ỏ": u"o", u"Ǒ": u"o",
       u"Ṕ": u"p", u"Ŗ": u"r", u"Û": u"u", u"ở": u"o", u"ǡ": u"a", u"Ṥ": u"s",
       u"ë": u"e", u"ữ": u"u", u"p": u"p", u"Ṵ": u"u", u"Ŷ": u"y", u"û": u"u",
       u"ā": u"a", u"Ẅ": u"w", u"ȇ": u"e", u"ḏ": u"d", u"ȗ": u"u", u"ḟ": u"f",
       u"ġ": u"g", u"Ấ": u"a", u"ȧ": u"a", u"ḯ": u"i", u"Ẵ": u"a", u"ḿ": u"m",
       u"À": u"a", u"Ễ": u"e", u"ṏ": u"o", u"ő": u"o", u"Ổ": u"o", u"ǖ": u"u",
       u"ṟ": u"r", u"š": u"s", u"à": u"a", u"Ụ": u"u", u"Ǧ": u"g", u"k": u"k",
       u"ṯ": u"t", u"ű": u"u", u"Ỵ": u"y", u"ṿ": u"v", u"Ā": u"a", u"Ȃ": u"a",
       u"ẅ": u"w", u"Ḋ": u"d", u"Ȓ": u"r", u"Ḛ": u"e", u"Ġ": u"g", u"ấ": u"a",
       u"Ḫ": u"h", u"İ": u"i", u"Ȳ": u"y", u"ẵ": u"a", u"Ḻ": u"l", u"Á": u"a",
       u"ễ": u"e", u"Ṋ": u"n", u"Ñ": u"n", u"Ő": u"o", u"ổ": u"o", u"Ǜ": u"u",
       u"Ṛ": u"r", u"á": u"a", u"Š": u"s", u"ụ": u"u", u"f": u"f", u"ǫ": u"o",
       u"Ṫ": u"t", u"ñ": u"n", u"Ű": u"u", u"ỵ": u"y", u"v": u"v", u"ǻ": u"a",
       u"Ṻ": u"u", u"ḅ": u"b", u"ċ": u"c", u"Ẋ": u"x", u"ȍ": u"o", u"ḕ": u"e",
       u"ě": u"e", u"Ơ": u"o", u"ḥ": u"h", u"ī": u"i", u"Ẫ": u"a", u"ȭ": u"o",
       u"ư": u"u", u"ḵ": u"k", u"Ļ": u"l", u"Ẻ": u"e", u"ṅ": u"n", u"Ị": u"i",
       u"ǐ": u"i", u"ṕ": u"p", u"Ö": u"o", u"ś": u"s", u"Ớ": u"o", u"a": u"a",
       u"Ǡ": u"a", u"ṥ": u"s", u"ū": u"u", u"Ừ": u"u", u"q": u"q", u"ǰ": u"j",
       u"ṵ": u"u", u"ö": u"o", u"Ż": u"z", u"Ȁ": u"a", u"ẃ": u"w", u"Ă": u"a",
       u"Ḉ": u"c", u"Ȑ": u"r", u"Ē": u"e", u"Ḙ": u"e", u"ả": u"a", u"Ģ": u"g",
       u"Ḩ": u"h", u"Ȱ": u"o", u"ẳ": u"a", u"Ḹ": u"l", u"ể": u"e", u"Ç": u"c",
       u"Ṉ": u"n", u"Ǎ": u"a", u"ồ": u"o", u"Ṙ": u"r", u"ợ": u"o", u"Ţ": u"t",
       u"ç": u"c", u"Ṩ": u"s", u"ǭ": u"o", u"l": u"l", u"ỳ": u"y", u"Ų": u"u",
       u"Ṹ": u"u", u"ḃ": u"b", u"Ẉ": u"w", u"ȋ": u"i", u"č": u"c", u"ḓ": u"d",
       u"ẘ": u"w", u"ț": u"t", u"ĝ": u"g", u"ḣ": u"h", u"Ẩ": u"a", u"ȫ": u"o",
       u"ĭ": u"i", u"ḳ": u"k", u"Ẹ": u"e", u"Ľ": u"l", u"ṃ": u"m", u"Ỉ": u"i",
       u"ō": u"o", u"Ì": u"i", u"ṓ": u"o", u"ǒ": u"o", u"Ộ": u"o", u"ŝ": u"s",
       u"Ü": u"u", u"ṣ": u"s", u"g": u"g", u"Ứ": u"u", u"ŭ": u"u", u"ì": u"i",
       u"ṳ": u"u", u"w": u"w", u"Ỹ": u"y", u"Ž": u"z", u"ü": u"u", u"Ȇ": u"e",
       u"ẉ": u"w", u"Č": u"c", u"Ḏ": u"d", u"Ȗ": u"u", u"ẙ": u"y", u"Ĝ": u"g",
       u"Ḟ": u"f", u"Ȧ": u"a", u"ẩ": u"a", u"Ĭ": u"i", u"Ḯ": u"i", u"ẹ": u"e",
       u"ļ": u"l", u"Ḿ": u"m", u"ỉ": u"i", u"Í": u"i", u"Ō": u"o", u"Ṏ": u"o",
       u"Ǘ": u"u", u"ộ": u"o", u"Ý": u"y", u"Ŝ": u"s", u"Ṟ": u"r", u"b": u"b",
       u"ǧ": u"g", u"ứ": u"u", u"í": u"i", u"Ŭ": u"u", u"Ṯ": u"t", u"r": u"r",
       u"ỹ": u"y", u"ý": u"y", u"ż": u"z", u"Ṿ": u"v", u"ȁ": u"a", u"ć": u"c",
       u"ḉ": u"c", u"Ẏ": u"y", u"ȑ": u"r", u"ė": u"e", u"ḙ": u"e", u"ḩ": u"h",
       u"Ắ": u"a", u"ȱ": u"o", u"ķ": u"k", u"ḹ": u"l", u"Ế": u"e", u"Â": u"a",
       u"Ň": u"n", u"ṉ": u"n", u"Ỏ": u"o", u"Ò": u"o", u"ŗ": u"r", u"ṙ": u"r",
       u"ǜ": u"u", u"Ở": u"o", u"â": u"a", u"ṩ": u"s", u"m": u"m", u"Ǭ": u"o",
       u"Ữ": u"u", u"ò": u"o", u"ŷ": u"y", u"ṹ": u"u", u"Ȅ": u"e", u"ẇ": u"w",
       u"Ḍ": u"d", u"Ď": u"d", u"Ȕ": u"u", u"ẗ": u"t", u"Ḝ": u"e", u"Ğ": u"g",
       u"ầ": u"a", u"Ḭ": u"i", u"Į": u"i", u"ặ": u"a", u"Ḽ": u"l", u"ľ": u"l",
       u"Ã": u"a", u"ệ": u"e", u"Ṍ": u"o", u"Ŏ": u"o", u"Ó": u"o", u"ỗ": u"o",
       u"Ǚ": u"u", u"Ṝ": u"r", u"Ş": u"s", u"ã": u"a", u"ủ": u"u", u"ǩ": u"k",
       u"h": u"h", u"Ṭ": u"t", u"Ů": u"u", u"ó": u"o", u"ỷ": u"y", u"ǹ": u"n",
       u"x": u"x", u"Ṽ": u"v", u"ž": u"z", u"ḇ": u"b", u"ĉ": u"c", u"Ẍ": u"x",
       u"ȏ": u"o", u"ḗ": u"e", u"ę": u"e", u"ȟ": u"h", u"ḧ": u"h", u"ĩ": u"i",
       u"Ậ": u"a", u"ȯ": u"o", u"ḷ": u"l", u"Ĺ": u"l", u"Ẽ": u"e", u"ṇ": u"n",
       u"È": u"e", u"Ọ": u"o", u"ǎ": u"a", u"ṗ": u"p", u"ř": u"r", u"Ờ": u"o",
       u"Ǟ": u"a", u"c": u"c", u"ṧ": u"s", u"ũ": u"u", u"è": u"e", u"Ử": u"u",
       u"s": u"s", u"ṷ": u"u", u"Ź": u"z", u"Ḃ": u"b", u"Ĉ": u"c", u"Ȋ": u"i",
       u"ẍ": u"x", u"Ḓ": u"d", u"Ę": u"e", u"Ț": u"t", u"쎟": u"s", u"Ḣ": u"h",
       u"Ĩ": u"i", u"Ȫ": u"o", u"ậ": u"a", u"Ḳ": u"k", u"ẽ": u"e", u"Ṃ": u"m",
       u"É": u"e", u"ň": u"n", u"ọ": u"o", u"Ǔ": u"u", u"Ṓ": u"o", u"Ù": u"u",
       u"Ř": u"r", u"ờ": u"o", u"Ṣ": u"s", u"é": u"e", u"Ũ": u"u", u"ử": u"u",
       u"n": u"n", u"Ṳ": u"u", u"ù": u"u", u"Ÿ": u"y", u"ă": u"a", u"Ẃ": u"w",
       u"ȅ": u"e", u"ḍ": u"d", u"ē": u"e", u"ȕ": u"u", u"ḝ": u"e", u"ģ": u"g",
       u"Ả": u"a", u"ḭ": u"i", u"Ẳ": u"a", u"ḽ": u"l", u"Ń": u"n", u"Ể": u"e",
       u"ṍ": u"o", u"Î": u"i", u"Ồ": u"o", u"ǘ": u"u", u"ṝ": u"r", u"ţ": u"t",
       u"Ợ": u"o", u"i": u"i", u"Ǩ": u"k", u"ṭ": u"t", u"î": u"i", u"ų": u"u",
       u"Ỳ": u"y", u"y": u"y", u"Ǹ": u"n", u"ṽ": u"v", u"Ḁ": u"a", u"Ȉ": u"i",
       u"ẋ": u"x", u"Ċ": u"c", u"Ḑ": u"d", u"Ș": u"s", u"Ě": u"e", u"Ḡ": u"g",
       u"Ȩ": u"e", u"ẫ": u"a", u"Ī": u"i", u"Ḱ": u"k", u"ẻ": u"e", u"ĺ": u"l",
       u"Ṁ": u"m", u"ị": u"i", u"Ï": u"i", u"Ṑ": u"o", u"Ǖ": u"u", u"ớ": u"o",
       u"Ś": u"s", u"ß": u"s", u"Ṡ": u"s", u"d": u"d", u"ừ": u"u", u"Ū": u"u",
       u"ï": u"i", u"Ṱ": u"t", u"ǵ": u"g", u"t": u"t", u"ź": u"z", u"ÿ": u"y",
       u"Ẁ": u"w", u"ȃ": u"a", u"ą": u"a", u"ḋ": u"d", u"ȓ": u"r", u"ĕ": u"e",
       u"ḛ": u"e", u"Ạ": u"a", u"ĥ": u"h", u"ḫ": u"h", u"Ằ": u"a", u"ȳ": u"y",
       u"ĵ": u"j", u"ḻ": u"l", u"Ề": u"e", u"Ņ": u"n", u"Ä": u"a", u"ṋ": u"n",
       u"Ố": u"o", u"ŕ": u"r", u"Ô": u"o", u"ṛ": u"r", u"ǚ": u"u", u"Ỡ": u"o",
       u"ť": u"t", u"ä": u"a", u"ṫ": u"t", u"Ǫ": u"o", u"o": u"o", u"Ự": u"u",
       u"ŵ": u"w", u"ô": u"o", u"ṻ": u"u", u"Ǻ": u"a", u"ẁ": u"w", u"Ą": u"a",
       u"Ḇ": u"b", u"Ȏ": u"o", u"Ĕ": u"e", u"Ḗ": u"e", u"Ȟ": u"h", u"ạ": u"a",
       u"Ĥ": u"h", u"Ḧ": u"h", u"Ư": u"u", u"Ȯ": u"o", u"ằ": u"a", u"Ĵ": u"j",
       u"Ḷ": u"l", u"ề": u"e", u"Å": u"a", u"ń": u"n", u"Ṇ": u"n", u"Ǐ": u"i",
       u"ố": u"o", u"Õ": u"o", u"Ŕ": u"r", u"Ṗ": u"p", u"ǟ": u"a", u"ỡ": u"o",
       u"å": u"a", u"Ť": u"t", u"Ṧ": u"s", u"j": u"j", u"ự": u"u", u"õ": u"o",
       u"Ŵ": u"w", u"Ṷ": u"u", u"z": u"z", u"ḁ": u"a", u"Ẇ": u"w", u"ȉ": u"i",
       u"ď": u"d", u"ḑ": u"d", u"ẖ": u"h", u"ș": u"s", u"ğ": u"g", u"ḡ": u"g",
       u"Ầ": u"a", u"ȩ": u"e", u"į": u"i", u"ḱ": u"k", u"Ặ": u"a", u"ṁ": u"m",
       u"Ệ": u"e", u"Ê": u"e", u"ŏ": u"o", u"ṑ": u"o", u"ǔ": u"u", u"Ỗ": u"o",
       u"Ú": u"u", u"ş": u"s", u"ṡ": u"s", u"e": u"e", u"Ủ": u"u", u"ê": u"e",
       u"ů": u"u", u"ṱ": u"t", u"u": u"u", u"Ǵ": u"g", u"Ỷ": u"y", u"ú": u"u",
       u"0": u"0", u"1": u"1", u"2": u"2", u"3": u"3", u"4": u"4", u"5": u"5",
       u"6": u"6", u"7": u"7", u"8": u"8", u"9": u"9"}

characters = "0123456789_abcdefghijklmnopqrstuvwxyz"

def normalize(str):
    global normalization_table
    nt = normalization_table # optimization

    str2 = u''
    for c in unicode(str).lower():
        try:
            str2 += nt[c]
        except KeyError:
            str2 += '_'
    # XXX depending on speed tests (and relevancy), replace by
    # return ''.join(nt[c] if c in nt else '_' for c in unicode(str).lower())
    return str2
