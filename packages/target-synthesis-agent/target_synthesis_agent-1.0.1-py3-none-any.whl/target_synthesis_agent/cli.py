"""
Command Line Interface for the Target Synthesis Agent.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Any

from .agent import TargetSynthesisAgent
from .config import TargetSynthesisConfig


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Target Synthesis Agent - AI-powered target variable creation and synthesis"
    )
    
    parser.add_argument(
        "--data", "-d",
        required=True,
        help="Path to input data file (CSV, Excel, or Parquet)"
    )
    
    parser.add_argument(
        "--business-context", "-b",
        type=json.loads,
        default="{}",
        help="Business context in JSON format (e.g., '{\"domain\": \"healthcare\", \"problem\": \"patient outcome prediction\"}')"
    )
    
    parser.add_argument(
        "--target-requirements", "-r",
        type=json.loads,
        default="{}",
        help="Target requirements in JSON format"
    )
    
    parser.add_argument(
        "--constraints", "-c",
        type=json.loads,
        default="{}",
        help="Constraints in JSON format (e.g., '{\"time_constraint\": \"2 weeks\"}')"
    )
    
    parser.add_argument(
        "--output", "-o",
        help="Output file path for results (JSON format)"
    )
    
    parser.add_argument(
        "--config", "-f",
        help="Path to configuration file (YAML/JSON)"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    try:
        # Load configuration if provided
        config = None
        if args.config:
            config = TargetSynthesisConfig.parse_file(args.config)
        
        # Initialize agent
        agent = TargetSynthesisAgent(config=config)
        
        # Prepare task data
        task_data = {
            "data": args.data,
            "business_context": args.business_context,
            "target_requirements": args.target_requirements,
            "constraints": args.constraints
        }
        
        # Execute task
        print(f"Executing target synthesis task...")
        print(f"Data: {args.data}")
        print(f"Business Context: {args.business_context}")
        print(f"Target Requirements: {args.target_requirements}")
        print(f"Constraints: {args.constraints}")
        print("-" * 50)
        
        result = agent.execute_task(task_data)
        
        if result["success"]:
            print("✅ Target synthesis completed successfully!")
            print("\n📊 Results Summary:")
            
            result_data = result["result"]
            print(f"Dataset: {result_data['dataset_name']}")
            print(f"Available Columns: {len(result_data['available_columns'])}")
            print(f"Synthesized Targets: {len(result_data['synthesized_targets'])}")
            
            # Display recommended target
            recommended = result_data['recommended_target']
            print(f"\n🏆 Recommended Target: {recommended['name']}")
            print(f"   Type: {recommended['target_type']}")
            print(f"   Confidence: {recommended['confidence_score']:.2f}")
            print(f"   Strategy: {recommended['synthesis_strategy']}")
            print(f"   Description: {recommended['description'][:100]}...")
            
            # Display alternative targets
            if result_data['alternative_targets']:
                print(f"\n🔍 Alternative Targets:")
                for i, alt in enumerate(result_data['alternative_targets'][:3], 1):
                    print(f"{i}. {alt['name']} ({alt['target_type']}) - Confidence: {alt['confidence_score']:.2f}")
            
            # Display synthesis insights
            print(f"\n💡 Synthesis Insights:")
            for insight in result_data['synthesis_insights'][:3]:
                print(f"   • {insight}")
            
            # Display implementation plan
            print(f"\n📋 Implementation Plan:")
            for i, step in enumerate(result_data['implementation_plan'][:5], 1):
                print(f"{i}. {step}")
            
            # Save output if requested
            if args.output:
                output_path = Path(args.output)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                
                with open(output_path, 'w') as f:
                    json.dump(result, f, indent=2, default=str)
                
                print(f"\n💾 Results saved to: {args.output}")
            
            # Print full results if verbose
            if args.verbose:
                print("\n📄 Full Results:")
                print(json.dumps(result, indent=2, default=str))
                
        else:
            print(f"❌ Target synthesis failed: {result['error']}")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
