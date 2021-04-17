from importlib.resources import read_text

def xml_data():
    return read_text('pricehist.resources', 'list_one.xml')
