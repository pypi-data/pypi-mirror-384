from typing import List

from maqet.logger import LOG


class Arguments:
    @staticmethod
    def split_args(*args: str) -> list[str]:
        """
        Split args by spaces and return as list
        """
        return [
            a_splitted
            for a in args
            for a_splitted in a.split(' ')
        ]

    @staticmethod
    def parse_options(arg, stack=[], key_only=False):
        if not isinstance(arg, (list, dict)):
            if len(stack) > 0:
                if key_only:
                    return '.'.join(stack) + f'.{arg}'
                else:
                    return '.'.join(stack) + f'={arg}'
            else:
                return arg

        options = []
        if isinstance(arg, list):
            for v in arg:
                if isinstance(arg, (list, dict)):
                    options.append(Arguments.parse_options(
                        v, stack, key_only=True))
                else:
                    options.append('.'.join(stack) + f'.{v}')

        elif isinstance(arg, dict):
            for k, v in arg.items():
                if isinstance(arg, (list, dict)):
                    options.append(Arguments.parse_options(
                        v, stack+[k], key_only=False))
                else:
                    option = '.'.join(stack) + f'={v}'
                    options.append(option)
        return ','.join(options)

    @staticmethod
    def parse_args(*args) -> List[str]:
        final_args = []

        LOG.debug(f'Parsing {args}')

        for arg in args:
            if type(arg) is str:
                argument = f'-{arg}'
            else:
                if isinstance(arg, dict):
                    al = list(arg.items())
                else:
                    al = list(args)
                if len(al) == 1:
                    argument = (f"-{al[0][0]}"
                                f" {Arguments.parse_options(al[0][1])}")
                else:
                    arg = al[0][0]
                    subarg = dict(al[1:])
                    argument = (f"-{al[0][0]} "
                                f"{al[0][1]},"
                                f"{Arguments.parse_options(subarg)}")
            final_args.append(argument)

        return Arguments.split_args(*final_args)

    def __call__(args: list):
        return Arguments.parse_args(args)
