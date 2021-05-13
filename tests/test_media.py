import base64
import unittest

import media


INPUT = 'input'
OUTPUT = 'output'
OUTPUT_Q30 = 'outputQ30'

IMG_PNG_DATA = [
    {
        INPUT: 'iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAYAAABzenr0AAAABmJLR0QA/wD/AP+gvaeTAAAACXBIWXMAAAsTAAALEwEAmpwYAAAAB3RJTUUH5AsFFDQAoQrKTAAAAB1pVFh0Q29tbWVudAAAAAAAQ3JlYXRlZCB3aXRoIEdJTVBkLmUHAAAAUklEQVRYw+3TsQoAIAiE4bve/51tiKAaoiVr+A/E9RPVkkIPUyQpohnG3isFsMb21FMAGdNuARnTHq9gvYmb8RdfAAAAAAAAAAAAAAAAAAAvUwE69Bou0cu+7AAAAABJRU5ErkJggg==',
        OUTPUT: 'iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAAfUlEQVR42u3Oqw1EIRCF4TPAFIBBIBA0gKIK+rqGuqgFjYYw1+x69iHvn0xy1JehnLMwM5xzSCnhui7MOXGaKqWg1ooxBkQEay0YY86B3jtaawghIMYIrTX23scAmFmUUmKtFe+9EJEAOD56ja9T70FEIKKPgf998AAP8Es3tDotwWG/JEsAAAAASUVORK5CYII=',
    }
]

IMG_JPG_DATA = [
    {
        INPUT: '/9j/4AAQSkZJRgABAQEASABIAAD//gATQ3JlYXRlZCB3aXRoIEdJTVD/2wBDAAMCAgMCAgMDAwMEAwMEBQgFBQQEBQoHBwYIDAoMDAsKCwsNDhIQDQ4RDgsLEBYQERMUFRUVDA8XGBYUGBIUFRT/2wBDAQMEBAUEBQkFBQkUDQsNFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBT/wgARCAAgACADAREAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAf/xAAUAQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIQAxAAAAGfEVAAAAAAAP/EABcQAAMBAAAAAAAAAAAAAAAAAAEEBUD/2gAIAQEAAQUCXpQxg//EABQRAQAAAAAAAAAAAAAAAAAAAED/2gAIAQMBAT8BB//EABQRAQAAAAAAAAAAAAAAAAAAAED/2gAIAQIBAT8BB//EAB8QAAICAQQDAAAAAAAAAAAAAAECAwQTERQhMEJDgf/aAAgBAQAGPwKliNOu61pFmazVyK0m3iCcYz7Ax+OfLQ9//8QAGRABAAIDAAAAAAAAAAAAAAAAAREhMUBB/9oACAEBAAE/ISrJzpeKEMZ7IOgf/9oADAMBAAIAAwAAABCSSSSSSST/xAAUEQEAAAAAAAAAAAAAAAAAAABA/9oACAEDAQE/EAf/xAAUEQEAAAAAAAAAAAAAAAAAAABA/9oACAECAQE/EAf/xAAXEAEBAQEAAAAAAAAAAAAAAAABETFA/9oACAEBAAE/EDSDHot93BbR4Af/2Q==',
        OUTPUT: '/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAMCAgMCAgMDAwMEAwMEBQgFBQQEBQoHBwYIDAoMDAsKCwsNDhIQDQ4RDgsLEBYQERMUFRUVDA8XGBYUGBIUFRT/2wBDAQMEBAUEBQkFBQkUDQsNFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBT/wAARCAAQABADAREAAhEBAxEB/8QAFgABAQEAAAAAAAAAAAAAAAAAAAYJ/8QAHRAAAgEFAQEAAAAAAAAAAAAAAgEDBREABAcSIf/EABQBAQAAAAAAAAAAAAAAAAAAAAD/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwDOTpfXN/p+tTIt2lUumLQKQgVLgKEC9hCDuHpivkIu6SuyJu98CFwGAwP/2Q==',
        OUTPUT_Q30: '/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDABsSFBcUERsXFhceHBsgKEIrKCUlKFE6PTBCYFVlZF9VXVtqeJmBanGQc1tdhbWGkJ6jq62rZ4C8ybqmx5moq6T/2wBDARweHigjKE4rK06kbl1upKSkpKSkpKSkpKSkpKSkpKSkpKSkpKSkpKSkpKSkpKSkpKSkpKSkpKSkpKSkpKSkpKT/wAARCAAQABADASIAAhEBAxEB/8QAFgABAQEAAAAAAAAAAAAAAAAAAAMF/8QAHBAAAgICAwAAAAAAAAAAAAAAAgABBBESUVLR/8QAFAEBAAAAAAAAAAAAAAAAAAAAAP/EABQRAQAAAAAAAAAAAAAAAAAAAAD/2gAMAwEAAhEDEQA/AMCxZKxAwQAOvWMceMEkP//Z',
    }
]


class MediaTest(unittest.TestCase):
    def setUp(self):
        pass

    def test_optimize_image_png(self):
        for imgdata in IMG_PNG_DATA:
            data = media.optimizeImage(base64.b64decode(imgdata[INPUT]), 'png', maxWidth=16)
            self.assertEqual(base64.b64encode(data), imgdata[OUTPUT].encode('ascii'))

            data = media.optimizeImage(base64.b64decode(imgdata[INPUT]), 'png', maxHeight=16)
            self.assertEqual(base64.b64encode(data), imgdata[OUTPUT].encode('ascii'))

            data = media.optimizeImage(base64.b64decode(imgdata[INPUT]), 'png', maxHeight=128, onlyShrink=True)
            self.assertFalse(data)

    def test_optimize_image_jpg(self):
        for imgdata in IMG_JPG_DATA:
            data = media.optimizeImage(base64.b64decode(imgdata[INPUT]), 'jpg', maxWidth=16)
            self.assertEqual(base64.b64encode(data), imgdata[OUTPUT].encode('ascii'))

            data = media.optimizeImage(base64.b64decode(imgdata[INPUT]), 'jpg', maxHeight=16)
            self.assertEqual(base64.b64encode(data), imgdata[OUTPUT].encode('ascii'))

            data = media.optimizeImage(base64.b64decode(imgdata[INPUT]), 'jpg', maxHeight=64)
            self.assertFalse(data)

            data = media.optimizeImage(base64.b64decode(imgdata[INPUT]), 'jpg', maxHeight=16, jpgQuality=30)
            self.assertEqual(base64.b64encode(data), imgdata[OUTPUT_Q30].encode('ascii'))
