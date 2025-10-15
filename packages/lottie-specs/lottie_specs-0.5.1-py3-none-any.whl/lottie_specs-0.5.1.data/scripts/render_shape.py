#!python
import sys
import math
import inspect
import pathlib
import argparse
import lottie

root = pathlib.Path(__file__).absolute().parent.parent
sys.path.append(str(root / "src"))
from lottie_specs.code_processing.loader import code_to_samples, SourceCode


class Bezier(lottie.objects.bezier.BezierView):
    def __init__(self, bez=None):
        super().__init__(bez or lottie.objects.bezier.Bezier(), False)

    def add_vertex(self, p: lottie.NVector):
        self.append(p)

    def set_in_tangent(self, p: lottie.NVector):
        self[-1].in_tangent = p

    def set_out_tangent(self, p: lottie.NVector):
        self[-1].out_tangent = p


def lerp(a, b, f):
    return a.lerp(b, f)


exec_globals = {
    "Color": lottie.Color,
    "Vector2D": lottie.NVector,
    "ELLIPSE_CONSTANT": 0.5519150244935105707435627,
    "Bezier": Bezier,
    "math": math,
    "lerp": lerp,
    "AbsoluteBezierPoint": lottie.objects.bezier.BezierPoint.from_absolute
}

default_args = {
    "NVector": lottie.NVector(200, 200),
    "float": 50,
    "int": 5,
}


def render_shape(func, args):
    anim = lottie.objects.Animation()
    lay = lottie.objects.layers.ShapeLayer()
    anim.add_layer(lay)
    lay.in_point = anim.in_point
    lay.out_point = anim.out_point

    shape = Bezier()
    func(shape, *args)
    lay.shapes.append(lottie.objects.shapes.Path(shape.bezier))
    lay.shapes.append(lottie.objects.shapes.Stroke(lottie.Color(1, 0.5, 0), 6))
    lay.shapes.append(lottie.objects.shapes.Fill(lottie.Color(1, 1, 0)))
    return anim


def render_modifier(func, args):
    anim = lottie.objects.Animation()
    lay = lottie.objects.layers.ShapeLayer()
    anim.add_layer(lay)
    lay.in_point = anim.in_point
    lay.out_point = anim.out_point

    # Half a circle combined with a 4 pointed star to have both curves and straight lines
    svg_d = "M 298.42641,213.5736 396,256 298.42641,298.42641 256,396 c -77.31986,0 -140,-62.68014 -140,-140 0,-77.31986 62.68014,-140 140,-140 z"
    svg_path = lottie.parsers.svg.importer.PathDParser(svg_d)
    svg_path.parse()
    in_shape = Bezier(svg_path.paths[0])
    out_shape = func(in_shape, *args)

    g1 = lottie.objects.shapes.Group()
    lay.shapes.append(g1)

    g1.add_shape(lottie.objects.shapes.Path(in_shape.bezier))
    g1.add_shape(lottie.objects.shapes.Stroke(lottie.Color(0.5, 0, 1), 6))

    g2 = lottie.objects.shapes.Group()
    lay.shapes.append(g2)

    g2.add_shape(lottie.objects.shapes.Path(out_shape.bezier))
    g2.add_shape(lottie.objects.shapes.Stroke(lottie.Color(1, 0.5, 0), 6))
    g2.add_shape(lottie.objects.shapes.Fill(lottie.Color(1, 1, 0)))
    return anim


def get_code(argv):
    if argv.docs:
        code = None
        with open(argv.docs) as f:
            for line in f:
                if "<algorithm>" in line:
                    code = ""
                elif "</algorithm>" in line:
                    if "def %s" % argv.func in code:
                        break
                    code = None
                elif code is not None:
                    code += line
        if code is None:
            print("Function %s not found" % argv.func, file=sys.stderr)
            sys.exit(1)
    elif argv.input:
        with open(argv.input) as f:
            code = f.read()
    else:
        print("Type code (end with ^D)")
        code = sys.stdin.read()

    data = SourceCode(code)

    if argv.view_code:
        if argv.view_code == "py":
            print(code)
        else:
            from source_translator.language_slug import slug_to_lang
            print(slug_to_lang(argv.view_code).convert(data))

    return data.ast


def prompt(name, type, default, no_prompt):
    if no_prompt:
        return default

    msg = name
    if type != "":
        msg += " [%s]" % type

    msg += " (%s)" % default

    sys.stdout.write(msg)
    sys.stdout.flush()
    return sys.stdin.readline().strip()


def main(argv):
    parsed = get_code(argv)

    local = {}
    exec(compile(parsed, "", "exec"), exec_globals, local)

    if argv.no_render:
        return

    default_func = next(iter(local.keys()))

    if argv.func is not None:
        func_name = argv.func
    else:
        func_name = prompt("Function name", "", default_func, argv.no_prompt)

    func = local[func_name or default_func]

    arg_spec = inspect.getfullargspec(func)

    given_args = {}

    if argv.args:
        for i in range(0, len(argv.args), 2):
            given_args[argv.args[i]] = argv.args[i + 1]

    args = []
    for i, arg in enumerate(arg_spec.args):
        if i == 0 and arg == "shape":
            continue
        annot = arg_spec.annotations[arg]
        typename = annot.__name__
        value = default_args[typename]
        if arg in given_args:
            value_raw = given_args[arg]
        else:
            value_raw = prompt(arg, typename, str(value).strip("[]"), argv.no_prompt)
        if value_raw:
            value = annot(*eval("[%s]" % value_raw))
        args.append(value)

    mode = argv.mode
    if mode is None:
        mode = prompt("Render mode", "shape|modifier", "shape", argv.no_prompt)

    if mode == "modifier":
        anim = render_modifier(func, args)
    else:
        anim = render_shape(func, args)

    print("Exporting to file://%s" % argv.output)
    lottie.exporters.core.export_embedded_html(anim, str(argv.output))


parser = argparse.ArgumentParser()
parser.add_argument("--docs", "-d", help="Docs file for the code input")
parser.add_argument("--input", "-i", help="File for the code input")
parser.add_argument("--func", "-f", default=None, help="Function name")
parser.add_argument("--no-prompt", "-np", action="store_true", help="Use default arguments, do not prompt")
parser.add_argument("--no-render", "-nr", action="store_true", help="Do not render the html")
parser.add_argument("--args", "-a", nargs="+", help="Argument values for the function")
parser.add_argument("--view-code", "-c", "-x", metavar="lang", help="Display rendered code")
parser.add_argument("--output", "-o", type=pathlib.Path, default=pathlib.Path("/tmp/out.html"))
parser.add_argument("--mode", "-m", choices=["shape", "modifier"], default=None)

if __name__ == "__main__":
    args = parser.parse_args()
    main(args)
