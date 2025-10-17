"""
Command-line interface for optimization-benchmarks package.

Provides utilities to evaluate benchmark functions from the command line,
supporting single evaluations, batch processing from CSV files, and 
function introspection.

Part of the optimization-benchmarks package[1].

References:
-----------
[1] Adorio, E. P. (2005). MVF - Multivariate Test Functions Library in C.
"""

import argparse
import sys
import json
import csv
import inspect

from optimization_benchmarks import functions


def get_available_functions():
    """
    Retrieve a sorted list of all available function names in the optimization_benchmarks.functions module.
    """
    funcs = [name for name, obj in inspect.getmembers(functions, inspect.isfunction)]
    return sorted(funcs)


def print_function_list():
    """
    Print the list of available functions, one per line.
    """
    funcs = get_available_functions()
    print("Available functions:")
    for name in funcs:
        print("  " + name)


def print_function_info(func_name):
    """
    Print the docstring information for the specified function.
    """
    if not hasattr(functions, func_name):
        print(f"Error: Function '{func_name}' not found.", file=sys.stderr)
        sys.exit(1)
    func = getattr(functions, func_name)
    doc = inspect.getdoc(func)
    if not doc:
        print(f"No documentation available for function '{func_name}'.")
    else:
        print(f"Function '{func_name}':\n{doc}")


def evaluate_function(func_name, values):
    """
    Evaluate the given function with the provided input values.
    Returns a dictionary containing the input and the result.
    """
    if not hasattr(functions, func_name):
        print(f"Error: Function '{func_name}' not found.", file=sys.stderr)
        sys.exit(1)
    func = getattr(functions, func_name)
    try:
        # Convert input values to float
        x = [float(v) for v in values]
    except ValueError as e:
        print(f"Error: Unable to convert input values to float: {e}", file=sys.stderr)
        sys.exit(1)
    result = func(x)
    return {"input": x, "result": result}


def evaluate_function_batch(func_name, input_file):
    """
    Evaluate the given function on a batch of input vectors from a CSV file.
    Returns a list of dictionaries with inputs and results.
    """
    results = []
    if not hasattr(functions, func_name):
        print(f"Error: Function '{func_name}' not found.", file=sys.stderr)
        sys.exit(1)
    func = getattr(functions, func_name)
    try:
        with open(input_file, 'r', newline='') as csvfile:
            reader = csv.reader(csvfile)
            for row_num, row in enumerate(reader, start=1):
                if not row:
                    continue  # Skip empty lines
                try:
                    x = [float(v) for v in row]
                except ValueError as e:
                    print(f"Error: Invalid number in CSV at line {row_num}: {e}", file=sys.stderr)
                    sys.exit(1)
                result = func(x)
                results.append({"input": x, "result": result})
    except FileNotFoundError:
        print(f"Error: Input file '{input_file}' not found.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error reading input file '{input_file}': {e}", file=sys.stderr)
        sys.exit(1)
    return results


def main():
    """
    Entry point for the optimization_benchmarks CLI.
    """
    parser = argparse.ArgumentParser(
        description="Command-line interface for evaluating optimization benchmark functions.",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python -m optimization_benchmarks.cli --function ackley --values 0 0 0\n"
            "  python -m optimization_benchmarks.cli --function rastrigin --input points.csv --output results.json\n"
            "  python -m optimization_benchmarks.cli --list\n"
            "  python -m optimization_benchmarks.cli --info ackley"
        )
    )
    parser.add_argument('--list', action='store_true', help="List all available functions")
    parser.add_argument('--info', metavar='FUNCTION', help="Show documentation for the specified function")
    parser.add_argument('--function', metavar='FUNCTION', help="Name of the function to evaluate")
    parser.add_argument('--values', metavar='N', nargs='+', help="Input values for single evaluation (space-separated)")
    parser.add_argument('--input', metavar='FILE', help="CSV file with input vectors for batch evaluation")
    parser.add_argument('--output', metavar='FILE', help="Output file to write results in JSON format")

    args = parser.parse_args()

    # Handle --list
    if args.list:
        if args.info or args.function or args.values or args.input or args.output:
            print("Error: --list cannot be combined with other options.", file=sys.stderr)
            sys.exit(1)
        print_function_list()
        sys.exit(0)

    # Handle --info
    if args.info is not None:
        if args.function or args.values or args.input or args.output:
            print("Error: --info cannot be combined with other options.", file=sys.stderr)
            sys.exit(1)
        print_function_info(args.info)
        sys.exit(0)

    # From here, require --function
    if not args.function:
        print("Error: --function is required for evaluation.", file=sys.stderr)
        parser.print_usage(sys.stderr)
        sys.exit(1)

    func_name = args.function

    # Determine evaluation mode
    if args.values and args.input:
        print("Error: --values and --input cannot be used together.", file=sys.stderr)
        sys.exit(1)
    if not args.values and not args.input:
        print("Error: Either --values or --input must be provided for function evaluation.", file=sys.stderr)
        parser.print_usage(sys.stderr)
        sys.exit(1)

    output_data = {"function": func_name}

    # Single evaluation
    if args.values:
        result_entry = evaluate_function(func_name, args.values)
        output_data["result"] = result_entry["result"]
        output_data["input"] = result_entry["input"]

    # Batch evaluation
    elif args.input:
        results = evaluate_function_batch(func_name, args.input)
        output_data["results"] = results

    # Output results
    output_json = json.dumps(output_data, indent=2)
    if args.output:
        try:
            with open(args.output, 'w') as f:
                f.write(output_json)
        except Exception as e:
            print(f"Error writing to output file '{args.output}': {e}", file=sys.stderr)
            sys.exit(1)
    else:
        print(output_json)


if __name__ == "__main__":
    main()
