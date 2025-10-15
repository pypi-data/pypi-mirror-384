import argparse
import json
from .core.workflow import Workflow
from .core.registry import registry


def main():
    parser = argparse.ArgumentParser(description='Execute AgentUI workflows')
    parser.add_argument('workflow_file', help='Path to workflow JSON file')
    parser.add_argument('--output', help='Output file for results (JSON)')

    args = parser.parse_args()

    try:
        # Load workflow from JSON file
        with open(args.workflow_file, 'r') as f:
            workflow_data = json.load(f)

        # Create and execute workflow
        workflow_json = json.dumps(workflow_data)
        workflow = Workflow.from_json(workflow_json, registry.get_all_types())

        print(f"Executing workflow with {len(workflow.nodes)} nodes...")
        results = workflow.execute()

        print("✅ Workflow executed successfully!")

        # Print results
        for node_id, result in results.items():
            print(f"\n{result['type']} ({node_id}):")
            for output_name, output_value in result['outputs'].items():
                if hasattr(output_value, '__class__'):
                    print(f"  {output_name}: {output_value.__class__.__name__}")
                else:
                    print(f"  {output_name}: {output_value}")

        # Save results if output file specified
        if args.output:
            # Convert PIL Images to strings for JSON serialization
            json_results = {}
            for node_id, result in results.items():
                json_results[node_id] = {
                    'type': result['type'],
                    'outputs': {}
                }
                for output_name, output_value in result['outputs'].items():
                    if hasattr(output_value, 'save'):  # PIL Image
                        json_results[node_id]['outputs'][output_name] = str(output_value)
                    else:
                        json_results[node_id]['outputs'][output_name] = output_value

            with open(args.output, 'w') as f:
                json.dump(json_results, f, indent=2)
            print(f"\nResults saved to {args.output}")

    except Exception as e:
        print(f"❌ Error: {e}")
        return 1

    return 0


if __name__ == '__main__':
    exit(main())