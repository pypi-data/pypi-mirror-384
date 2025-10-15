import argparse
import configparser
import sys
import logging
import jinja2

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s %(levelname)-5.5s [%(name)s:%(lineno)s][%(threadName)s] %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


def read_variable_file(filename):
    parser = configparser.ConfigParser()
    parser.read(filename)
    return parser

def parse_args(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'template',
        help='Template jinja2 file, e.g., development.ini.jinja2',
    )
    parser.add_argument(
        'variable',
        help='Variable ini file, e.g., secrets.ini',
    )
    parser.add_argument(
        '-o', '--output',
        help='Output file, default to secrets_<name of template>.ini',
    )

    return parser.parse_args(argv[1:])

def main(argv=sys.argv):
    args = parse_args(argv)
    config = read_variable_file(args.variable)

    vars_dict = {s:dict(config.items(s)) for s in config.sections()}
    logger.debug(vars_dict)

    template = jinja2.Template(open(args.template).read())
    output = template.render(vars_dict)
    if args.output is None:
        output_file = 'secrets_{}.ini'.format(args.template.split('.')[0])
    else:
        output_file = args.output
    with open(output_file, 'w') as f:
        f.write(output)
        logger.info('Output file: %s', output_file)
        
