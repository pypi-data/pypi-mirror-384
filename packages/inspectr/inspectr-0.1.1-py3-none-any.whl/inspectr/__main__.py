import sys
import pathlib
import importlib


def main():
    if len(sys.argv) < 2:
        print("Usage: inspectr <subtool> [options] [files...]")
        sys.exit(1)

    subtool = sys.argv[1]
    remaining_args = sys.argv[2:]

    try:
        mod = importlib.import_module(f"inspectr.{subtool}")
    except ModuleNotFoundError:
        print(f"Unknown subtool: {subtool}")
        sys.exit(1)

    # Each subtool should define a `main(args)` function
    if not hasattr(mod, "main"):
        print(f"Subtool '{subtool}' does not define a main(args) function")
        sys.exit(1)

    files = []
    kwargs = {}
    
    # convert --option style options into keyword arguments
    i = 0
    while i < len(remaining_args):
        arg = remaining_args[i]
        if arg.startswith("--"):
            option_name = arg[2:].replace("-", "_")
            if i + 1 < len(remaining_args) and not remaining_args[i + 1].startswith("--"):
                value = remaining_args[i + 1]
                try:
                    kwargs[option_name] = int(value)
                except ValueError:
                    kwargs[option_name] = value
                i += 2
            else:
                kwargs[option_name] = True
                i += 1
        else:
            files.append(pathlib.Path(arg))
            i += 1
    
    mod.main(files, **kwargs)


if __name__ == "__main__":
    main()
