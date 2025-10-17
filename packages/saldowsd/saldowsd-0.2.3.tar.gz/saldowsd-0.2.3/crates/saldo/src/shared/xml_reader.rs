use std::{borrow::Cow, collections::BTreeMap, io::BufRead};

use quick_xml::events::{Event, attributes::Attributes};

pub struct XmlReader<R, C> {
    reader: quick_xml::NsReader<R>,
    content_handler: C,
}
pub type AttributeMap<'a> = BTreeMap<&'a [u8], Cow<'a, [u8]>>;
pub trait ContentHandler {
    fn start_element(&mut self, name: &[u8], attributes: AttributeMap<'_>);
    fn end_element(&mut self, name: &[u8]);
}

impl<R: BufRead, C> XmlReader<R, C> {
    pub fn new(reader: R, content_handler: C) -> Self {
        Self {
            reader: quick_xml::NsReader::from_reader(reader),
            content_handler,
        }
    }

    pub fn into_inner(self) -> C {
        let Self {
            reader: _,
            content_handler,
        } = self;
        content_handler
    }
}

fn collect_attributes<'a>(attributes: Attributes<'a>) -> BTreeMap<&'a [u8], Cow<'a, [u8]>> {
    let mut map = BTreeMap::new();
    for attr in attributes {
        if let Ok(attr) = attr {
            map.insert(attr.key.0, attr.value);
        } else {
            todo!("handle error")
        }
    }
    map
}

impl<R: BufRead, C: ContentHandler> XmlReader<R, C> {
    pub fn parse(&mut self) {
        let mut buf = Vec::new();
        loop {
            match self.reader.read_event_into(&mut buf) {
                Ok(Event::Start(e)) => {
                    log::trace!("read Start={:?}", e);
                    self.content_handler
                        .start_element(e.name().as_ref(), collect_attributes(e.attributes()));
                }
                Ok(Event::Empty(e)) => {
                    log::trace!("read Empty={:?}", e);
                    self.content_handler
                        .start_element(e.name().as_ref(), collect_attributes(e.attributes()));
                    self.content_handler.end_element(e.name().as_ref());
                }
                Ok(Event::Decl(e)) => log::trace!("read Decl={:?}", e),
                Ok(Event::End(e)) => {
                    log::trace!("read End={:?}", e);
                    self.content_handler.end_element(e.name().as_ref());
                }
                Ok(Event::Text(e)) => log::trace!("read Text={:?}", e),
                Ok(Event::Comment(e)) => log::trace!("read Comment={:?}", e),
                Ok(Event::Eof) => break,
                e => todo!("handle {:?}", e),
            }
        }
    }
}
