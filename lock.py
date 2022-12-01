import os
from os.path import basename
import pyzipper
from pyzipper import ZIP_STORED, ZIP_DEFLATED, ZIP_LZMA, ZIP_BZIP2
from pygame import init, time, display, sprite, rect, draw, mouse, font, event, quit, \
    KEYDOWN, K_ESCAPE, K_RETURN, K_BACKSPACE, QUIT

init()
clock = time.Clock()
width = 720
height = 480
win = display.set_mode((width, height))
display.set_caption("USB Drive Lock")
sliders = sprite.Group()
buttons = sprite.Group()
textboxes = sprite.Group()
font1 = "Courier New"

# editables are in a list, [0] is the value, [-1] is the names, and the rest are options
"""
screens:
'main'
'encrypt'
'encryptx'
'encrypty'
'decrypt'
'decryptx'
'encrypty'
'exit'
"""
screen = "main"
compression = [ZIP_STORED, ZIP_STORED, ZIP_DEFLATED, ZIP_LZMA, ZIP_BZIP2, {
    ZIP_STORED: "STORED[NONE]",
    ZIP_DEFLATED: "DEFLATED[LOW]",
    ZIP_LZMA: "LZMA[MED]",
    ZIP_BZIP2: "BZIP2[HIGH]",
}]
encryption = [128, 128, 192, 256, {
    128: "128",
    192: "192",
    256: "256",
}]

bg = (248, 237, 227)
secondary = (223, 211, 195)
primary = (208, 184, 168)
contrast = (125, 110, 131)


def zipitems(password, location, *exclusions):
    filecount = 0
    foldercount = 0
    blacklist = ['lock.exe', 'lock.app', 'encpwd.txt', 'readme.txt'] + [ex for ex in exclusions]

    try:
        open(location, 'x')
        os.remove(location)
    except OSError:
        changescreen('encryptx')
        return

    with pyzipper.AESZipFile(location, 'w', compression=compression[0], encryption=pyzipper.WZ_AES) as zipper:
        zipper.pwd = password
        zipper.encryption = encryption[0]
        for root, folders, files in os.walk(os.getcwd()):
            for filename in files:
                if filename not in blacklist:
                    path = os.path.join(root, filename)
                    zipper.write(path, basename(path))
                    filecount += 1
            for foldername in folders:
                if foldername not in blacklist:
                    path = os.path.join(root, foldername)
                    zipper.write(path, basename(path))
                    foldercount += 1

    genpwd(password, location)
    changescreen('encrypty')
    return filecount, foldercount


def unzipitems(password, location):
    try:
        open(location, 'r')
    except FileNotFoundError or PermissionError:
        changescreen('decryptx')
        return

    with pyzipper.AESZipFile(location) as zipper:
        zipper.pwd = password
        zipper.extractall(os.getcwd())
    changescreen('decrypty')


def genpwd(password, location="unknown"):
    try:
        with open(r"encpwd.txt", 'a') as file:
            if password is not None and password.strip() != "":
                file.write(f'{location[0]}: {password[0]}\n')
    except PermissionError:
        print("FileNotFound")


def changescreen(_screen="main", oldscreen=None):
    global screen

    valid = True
    if oldscreen is not None:
        for i in (s for s in textboxes if s.screen == oldscreen):
            if not i.valid:
                i.hastargeted = True
                valid = False

    if valid:
        screen = _screen


def prin(arg):
    print(arg)


class Slider(sprite.Sprite):
    def __init__(self, attr, bgpos, bgval=None, ptrval=None, name="default", fontsizes=None,
                 bgcolor=secondary, ptrcolor=primary, splitcolor=contrast, defval=0, _screen="main", markerthickness=3):
        super().__init__()
        if bgval is None:
            bgval = [300, 16]
        if ptrval is None:
            ptrval = [bgval[1] * 5 / 4, bgval[1] * 5 / 4]
        if fontsizes is None:
            fontsizes = [24, 18]
        self.bgrect = rect.Rect(bgpos[0], bgpos[1], bgval[0], bgval[1])
        self.ptrrect = rect.Rect(0, 0, ptrval[0], ptrval[1])
        self.name = name
        while len(attr[-1]) != len(attr[1:-1]):
            attr[-1].update({"default": "wawa"})
        self.bgcolor = bgcolor
        self.ptrcolor = ptrcolor
        self.splitcolor = splitcolor
        self.screen = _screen
        self.markerthickness = markerthickness

        self.attr = attr
        # width incremented by 1 to prevent indexing out of range for options
        self.options = (self.bgrect.width + 1) / len(attr[-1])
        self.value = defval * self.options
        self.attr[0] = self.attr[int(self.value // self.options) + 1]

        self.header = font.SysFont(font1, fontsizes[0], True).render(name, True, contrast)
        self.body = font.SysFont(font1, fontsizes[1], True)
        self.bodytext = self.body.render(self.attr[-1][self.attr[0]], True, contrast)

        self.targeted = False
        self.cantarget = True

        self.ptrrect.centerx = self.bgrect.left
        self.ptrrect.centery = self.bgrect.centery
        self.ptrrect.x += self.value

    def inrange(self):
        return (self.bgrect.left <= mouse.get_pos()[0] <= self.bgrect.right or
                self.ptrrect.left <= mouse.get_pos()[0] <= self.ptrrect.right) and \
               self.ptrrect.top <= mouse.get_pos()[1] <= self.ptrrect.bottom

    def update(self):
        if self.screen == screen:
            mspressed = mouse.get_pressed()[0]
            if not self.targeted and mspressed:
                if self.inrange() and self.cantarget:
                    self.targeted = True
                else:
                    self.cantarget = False
            if not mspressed:
                self.targeted = False
                self.cantarget = True

            if self.targeted:
                mousex = mouse.get_pos()[0]
                if mousex <= self.bgrect.left:
                    self.value = 0
                elif mousex >= self.bgrect.right:
                    self.value = self.bgrect.width
                else:
                    self.value = mousex - self.bgrect.left
                self.ptrrect.centerx = self.bgrect.left + self.value
                self.attr[0] = self.attr[int(self.value // self.options) + 1]
                self.bodytext = self.body.render(self.attr[-1][self.attr[0]], True, contrast)

            self.draw()

    def draw(self):
        draw.rect(win, self.bgcolor, self.bgrect)
        for i in range(1, int(self.bgrect.width // self.options) + 1):
            draw.rect(win, self.splitcolor, rect.Rect(
                self.bgrect.left + self.options * i - ((self.markerthickness - 1) / 2),
                self.bgrect.top, self.markerthickness, self.bgrect.height))
        draw.rect(win, self.ptrcolor, self.ptrrect)
        win.blit(self.header, self.header.get_rect(
            center=(self.bgrect.centerx, self.bgrect.top - self.header.get_size()[1] * 5 / 8)))
        win.blit(self.bodytext, self.bodytext.get_rect(
            center=(self.bgrect.centerx, self.bgrect.bottom + self.header.get_size()[1] / 2)))


class Button(sprite.Sprite):
    buttonpress = False

    def __init__(self, func, bgpos, *funcargs, bgval=None, border=-1, text="wawa", textsize=35,
                 bgcolors=None, textcolor=contrast, _screen="main"):
        super().__init__()
        if bgval is None:
            bgval = [125, 50]
        if bgcolors is None:
            bgcolors = [primary, secondary]
        self.bgrect = rect.Rect(bgpos[0], bgpos[1], bgval[0], bgval[1])
        self.bd = border
        self.bgcolors = bgcolors
        self.screen = _screen
        self.func = func
        self.funcargs = list(funcargs)
        self.text = font.SysFont(font1, textsize, True).render(text, True, textcolor)
        self.cantarget = True

    def inrange(self):
        return self.bgrect.left <= mouse.get_pos()[0] <= self.bgrect.right and \
               self.bgrect.top <= mouse.get_pos()[1] <= self.bgrect.bottom

    def update(self):
        if self.screen == screen:
            mspressed = mouse.get_pressed()[0]
            if mspressed:
                if self.cantarget and self.inrange():
                    if self.func is not None and not Button.buttonpress:
                        Button.buttonpress = True
                        itemflags = {}
                        for i, item in enumerate(self.funcargs):
                            if isinstance(item, str) and "/*" in item:
                                itemflags[i] = item
                                self.funcargs[i] = [s.text for s in textboxes if s.ident == item.replace("/*", "")]
                        self.func(*self.funcargs)
                        for i in itemflags.keys():
                            self.funcargs[i] = itemflags[i]
                else:
                    self.cantarget = False
            else:
                self.cantarget = True
                Button.buttonpress = False

            self.draw()

    def draw(self):
        draw.rect(win, self.bgcolors[1], rect.Rect(self.bgrect.left - self.bd, self.bgrect.top - self.bd,
                                                   self.bgrect.width + self.bd * 2,
                                                   self.bgrect.height + self.bd * 2))
        draw.rect(win, self.bgcolors[0], self.bgrect)
        win.blit(self.text, self.text.get_rect(center=self.bgrect.center))


class TextBox(sprite.Sprite):
    nextident = 0
    needfill = font.SysFont(font1, 15, True).render("textbox cannot be empty", True, (255, 0, 0))
    needext = font.SysFont(font1, 15, True).render("file extension required", True, (255, 0, 0))

    def __init__(self, bgpos, bgval=None, writable=True, reqs=None, createshell=False, ident=0,
                 childid=None, deletable=False, border=-1, title="wawa", text="", fontsizes=None, bgcolors=None,
                 textcolor=contrast, _screen="main"):
        super().__init__()
        if bgval is None:
            bgval = [300, 100]
        if reqs is None:
            reqs = [False, False]
        if fontsizes is None:
            fontsizes = [24, 20]
        if bgcolors is None:
            bgcolors = [primary, secondary]
        self.bgrect = rect.Rect(bgpos[0], bgpos[1], bgval[0], bgval[1])
        self.writable = writable
        self.reqs = {'filled': reqs[0], 'extension': reqs[1]}
        self.valid = False
        self.createshell = createshell
        self.ident = ident
        self.childid = self.nextident
        if self.writable:
            self.nextident += 1
            if childid is not None:
                self.childid = childid
        self.deletable = deletable
        self.bd = border
        self.bgcolors = bgcolors
        self.screen = _screen
        self.title = font.SysFont(font1, fontsizes[0], True).render(title, True, textcolor)
        self.text = text
        self.textfont = font.SysFont(font1, fontsizes[1], True)
        self.textcolor = textcolor
        self.textsurf = self.textfont.render(self.text, True, self.textcolor)

        self.targeted = False
        self.cantarget = True
        self.hastargeted = False

    def inrange(self):
        return self.bgrect.left <= mouse.get_pos()[0] <= self.bgrect.right and \
               self.bgrect.top <= mouse.get_pos()[1] <= self.bgrect.bottom

    def update(self, _event=None, ident=-1, delete=False):
        if self.screen == screen:
            mspressed = mouse.get_pressed()[0]
            if mspressed:
                if self.inrange() and self.cantarget:
                    self.targeted = True
                    self.hastargeted = True
                else:
                    self.targeted = False
                    self.cantarget = False
            if not mspressed:
                self.cantarget = True

            if _event is not None:
                if self.targeted and _event.type == KEYDOWN and self.writable:
                    if _event.key == K_ESCAPE:
                        self.targeted = False
                    elif _event.key == K_RETURN:
                        if self.createshell:
                            if self.text != "":
                                textboxes.update(ident=self.childid)
                                # noinspection PyTypeChecker
                                textboxes.add(TextBox([self.bgrect.left, self.bgrect.bottom + self.bd + 2],
                                                      writable=False, ident=self.childid, border=2, title="",
                                                      text=self.text, _screen=self.screen))
                                self.text = ""
                        else:
                            self.targeted = False
                    elif _event.key == K_BACKSPACE:
                        if self.text != "":
                            self.text = self.text[:-1]
                        else:
                            textboxes.update(ident=self.childid, delete=True)
                    else:
                        self.text += _event.unicode
                    self.textsurf = self.textfont.render(self.text, True, self.textcolor)
            if not self.writable and self.ident == ident:
                if not delete:
                    self.bgrect.top = self.bgrect.bottom
                else:
                    self.kill()

            self.bgrect.height = self.textsurf.get_height()
            self.draw()

    def draw(self):
        draw.rect(win, self.bgcolors[1], rect.Rect(self.bgrect.left - self.bd, self.bgrect.top - self.bd,
                                                   self.bgrect.width + self.bd * 2,
                                                   self.bgrect.height + self.bd * 2))
        draw.rect(win, self.bgcolors[0], self.bgrect)
        win.blit(self.title, self.title.get_rect(
            center=(self.bgrect.centerx, self.bgrect.top - (self.title.get_size()[1] + self.bd) * 5 / 8)))
        win.blit(self.textsurf, self.textsurf.get_rect(center=self.bgrect.center))

        if self.hastargeted and self.writable and not self.createshell:
            if self.reqs['filled'] and self.text == "":
                win.blit(self.needfill, self.needfill.get_rect(top=self.bgrect.bottom + self.bd,
                                                               centerx=self.bgrect.centerx))
                self.valid = False
            elif self.reqs['extension'] and self.text.find('.', 0, -1) == -1:
                win.blit(self.needext, self.needext.get_rect(top=self.bgrect.bottom + self.bd,
                                                             centerx=self.bgrect.centerx))
                self.valid = False
            else:
                self.valid = True


def redrawgamewindow():
    sliders.update()
    buttons.update()
    textboxes.update()
    display.flip()


# noinspection PyTypeChecker
sliders.add(Slider(compression, [25, 35], name="Compression", _screen='encrypt'),
            Slider(encryption, [405, 35], name="Encryption", _screen='encrypt'))
# noinspection PyTypeChecker
buttons.add(Button(changescreen, [65, 35], 'encrypt', bgval=[170, 75], border=10, text="ENCRYPT", _screen='main'),
            Button(changescreen, [65, 197.5], 'decrypt', bgval=[170, 75], border=10, text="DECRYPT", _screen='main'),
            Button(changescreen, [65, 360], 'exit', bgval=[170, 75], border=10, text="EXIT", _screen='main'),
            Button(changescreen, [60, 380], 'main', border=10, text="BACK", _screen='encrypt'),
            Button(zipitems, [530, 380], "/*passwordE", "/*locationE", "/*blklstE", border=10, text="GO",
                   _screen='encrypt'),
            Button(genpwd, [530, 300], "/*passwordE", "/*locationE", border=10, text="GEN PWD", textsize=25,
                   _screen='encrypt'),
            Button(changescreen, [60, 380], 'main', border=10, text="BACK", _screen='decrypt'),
            Button(unzipitems, [530, 380], "/*passwordD", "/*locationD", border=10, text="GO", _screen='decrypt'),
            # Button(changescreen, [60, 280], 'encrypty', border=10, text="test", _screen='encrypt'),
            # Button(changescreen, [60, 280], 'decrypty', border=10, text="test", _screen='decrypt'),
            Button(changescreen, [60, 380], 'encrypt', border=10, text="BACK", _screen='encryptx'),
            Button(changescreen, [60, 380], 'decrypt', border=10, text="BACK", _screen='decryptx'),
            Button(changescreen, [60, 380], 'main', border=10, text="BACK", _screen='encrypty'),
            Button(changescreen, [60, 380], 'main', border=10, text="BACK", _screen='decrypty'),
            Button(changescreen, [530, 380], 'exit', border=10, text="EXIT", _screen='encrypty'),
            Button(changescreen, [530, 380], 'exit', border=10, text="EXIT", _screen='decrypty'))
# noinspection PyTypeChecker
textboxes.add(TextBox([305, 50], writable=False, title="", text="encrypt and compress your files", bgcolors=[bg, bg]),
              TextBox([305, 75], writable=False, title="", text="defaults to no compression", bgcolors=[bg, bg]),
              TextBox([305, 212.5], writable=False, title="", text="decrypt with your password", bgcolors=[bg, bg]),
              TextBox([305, 237.5], writable=False, title="", text="also decompresses the files", bgcolors=[bg, bg]),
              TextBox([305, 375], writable=False, title="", text="USE FILE NAME EXTENSIONS", bgcolors=[bg, bg]),
              TextBox([305, 400], writable=False, title="", text="(like .py)", bgcolors=[bg, bg]),
              TextBox([25, 150], border=5, ident="passwordE", reqs=[True, False], title="password", _screen='encrypt'),
              TextBox([25, 255], border=5, ident="locationE", reqs=[True, True], title="location", _screen='encrypt'),
              TextBox([395, 150], createshell=True, childid="blklstE", border=5, title="blacklist", _screen='encrypt'),
              TextBox([210, 45], border=5, ident="passwordD", title="password", _screen='decrypt'),
              TextBox([210, 150], border=5, ident="locationD", title="location", _screen='decrypt'),
              TextBox([210, 50], writable=False, title="", text="ERROR: INVALID ZIP FILE NAME/LOCATION",
                      bgcolors=[bg, bg], _screen='encryptx'),
              TextBox([210, 50], writable=False, title="", text="ERROR: INVALID ZIP FILE LOCATION", bgcolors=[bg, bg],
                      _screen='decryptx'),
              TextBox([210, 50], writable=False, title="", text="ENCRYPTION FINISHED", bgcolors=[bg, bg],
                      _screen='encrypty'),
              TextBox([210, 50], writable=False, title="", text="DECRYPTION FINISHED", bgcolors=[bg, bg],
                      _screen='decrypty'))

run = True
while run:
    clock.tick(120)
    for _event in event.get():
        if _event.type == QUIT:
            run = False
        textboxes.update(_event)
    if screen == 'exit':
        run = False

    win.fill(bg)
    redrawgamewindow()
quit()
