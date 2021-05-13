import mimetypes


mimetypes_dict = {
    'audio/mpeg': 'mp2',
    'image/bmp': 'bmp',
    'image/gif': 'gif',
    'image/jpeg': 'jpg',
    'image/png': 'png',
    'image/svg+xml': 'svg',
    'image/tiff': 'tiff',
    'text/html': 'txt',
    'video/mpeg': 'mpg',
    'video/quicktime': 'mov',
    'video/webm': 'webm',
    'video/x-msvideo': 'avi',
    'video/x-sgi-movie': 'movie',
}


def guessExtension(s):
    if mimetypes_dict.get(s):
        return mimetypes_dict[s]

    e = mimetypes.guess_extension(s)
    return None if e is None else e[1:]
