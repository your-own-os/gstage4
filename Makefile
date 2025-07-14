prefix=/usr

all:

clean:
	find . -name *.pyc | xargs rm -f

install:
	install -d -m 0755 "$(DESTDIR)/$(prefix)/libexec/gstage4"
	cp -r libexec/* "$(DESTDIR)/$(prefix)/libexec/gstage4"
	chmod 755 "$(DESTDIR)/$(prefix)/libexec/gstage4/patch-repository"
	chmod 755 "$(DESTDIR)/$(prefix)/libexec/gstage4/portage-mrget"

.PHONY: all clean install
