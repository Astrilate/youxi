import random
import string
from PIL import Image, ImageFont, ImageDraw


class ImageCode:
    def rand_color(self):
        red = random.randint(32, 200)
        green = random.randint(22, 255)
        blue = random.randint(0, 200)
        return red, green, blue

    def gen_text(self):
        clist = random.sample(string.ascii_letters, 4)
        return ''.join(clist)

    def draw_lines(self, draw, num, width, height):
        for num in range(num):
            x1 = random.randint(0, width / 2)
            y1 = random.randint(0, height / 2)
            x2 = random.randint(0, width)
            y2 = random.randint(height / 2, height)
            draw.line(((x1, y1), (x2, y2)), fill='black', width=2)

    def draw_verify_code(self):
        code = self.gen_text()
        width, height = 120, 50
        im = Image.new('RGB', (width, height), 'white')
        font = ImageFont.truetype(font='arial.ttf', size=40)
        draw = ImageDraw.Draw(im)
        for i in range(4):
            draw.text((5 + random.randint(-3, 3) + 23 * i, 5 + random.randint(-3, 3)),
                      text=code[i], fill=self.rand_color(), font=font)
        self.draw_lines(draw, 4, width, height)
        return im, code


ImageCode().draw_verify_code()
