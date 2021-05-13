import io

from PIL import Image


imageMimetypes = {
    'image/bmp': 'bmp',
    'image/gif': 'gif',
    'image/jpeg': 'jpeg',
    'image/png': 'png',
    'image/svg+xml': 'svg',
    'image/tiff': 'tiff',
}


def optimizeImage(data, format, maxWidth=None, maxHeight=None, jpgQuality=None, onlyShrink=False):
    sio = io.BytesIO(data)
    img = Image.open(sio)
    changed = False

    if maxWidth is not None or maxHeight is not None:
        if maxWidth is None:
            maxWidth = img.width
        if maxHeight is None:
            maxHeight = img.height

        if maxWidth < img.width or maxHeight < img.height:
            img.thumbnail((maxWidth, maxHeight), Image.ANTIALIAS)
            changed = True

    tmpbuf = io.BytesIO()
    if format in ['jpg', 'jpeg']:
        if jpgQuality is None:
            jpgQuality = 'keep'
        else:
            changed = True

        if changed:
            img.save(tmpbuf, format='jpeg', optimize=True, quality=jpgQuality)
    else:
        if changed:
            img.save(tmpbuf, format=format, optimize=True)

    if changed:
        didShrink = sio.getbuffer().nbytes > tmpbuf.getbuffer().nbytes
        if onlyShrink and didShrink or not onlyShrink:
            return tmpbuf.getvalue()

        if not didShrink:
            return None

    return False
