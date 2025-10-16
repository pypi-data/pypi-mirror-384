#!/usr/bin/env python3
"""
Featrix Sphere CLI

Command-line interface for the Featrix Sphere API client.
"""

import argparse
import sys
from pathlib import Path
from .client import FeatrixSphereClient


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Featrix Sphere API Client - Transform CSV to ML models",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Upload data and create session
  featrix upload data.csv --server YOUR_SERVER_URL
  
  # Test predictions on CSV
  featrix test SESSION_ID test.csv target_column --server YOUR_SERVER_URL
  
  # Make single prediction from JSON
  featrix predict SESSION_ID '{"feature": "value"}' --server YOUR_SERVER_URL
  
  # Make predictions from CSV file
  featrix predict SESSION_ID test.csv --server YOUR_SERVER_URL --sample-size 50
        """
    )
    
    parser.add_argument("--server", default="https://sphere-api.featrix.com",
                       help="Featrix Sphere server URL")
    parser.add_argument("--compute-cluster", type=str, default=None,
                       help="Compute cluster port for X-Sphere-Compute header")
    parser.add_argument("--version", action="version", 
                       version=f"featrixsphere {__import__('featrixsphere').__version__}")
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Upload command
    upload_parser = subparsers.add_parser("upload", help="Upload CSV and create session")
    upload_parser.add_argument("csv_file", help="CSV file to upload")
    upload_parser.add_argument("--wait", action="store_true", 
                              help="Wait for training to complete")
    
    # Test command
    test_parser = subparsers.add_parser("test", help="Test predictions on CSV")
    test_parser.add_argument("session_id", help="Session ID")
    test_parser.add_argument("csv_file", help="CSV file to test")
    test_parser.add_argument("target_column", help="Target column name")
    test_parser.add_argument("--sample-size", type=int, default=100,
                            help="Number of records to test (default: 100)")
    
    # Predict command
    predict_parser = subparsers.add_parser("predict", help="Make single prediction")
    predict_parser.add_argument("session_id", help="Session ID")
    predict_parser.add_argument("input", help="JSON record or CSV file to predict")
    predict_parser.add_argument("--sample-size", type=int, default=1000,
                               help="Number of records to predict from CSV (default: 1000)")
    predict_parser.add_argument("-v", "--verbose", action="store_true",
                               help="Print full results structure")
    
    # Status command
    status_parser = subparsers.add_parser("status", help="Check session status")
    status_parser.add_argument("session_id", help="Session ID")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    try:
        client = FeatrixSphereClient(args.server, compute_cluster=args.compute_cluster)
        
        if args.command == "upload":
            return cmd_upload(client, args)
        elif args.command == "test":
            return cmd_test(client, args)
        elif args.command == "predict":
            return cmd_predict(client, args)
        elif args.command == "status":
            return cmd_status(client, args)
        else:
            print(f"Unknown command: {args.command}")
            return 1
            
    except Exception as e:
        print(f"Error: {e}")
        return 1


def cmd_upload(client, args):
    """Handle upload command."""
    csv_file = Path(args.csv_file)
    if not csv_file.exists():
        print(f"File not found: {csv_file}")
        return 1
    
    print(f"Uploading {csv_file} to {client.base_url}...")
    session = client.upload_file_and_create_session(csv_file)
    
    print(f"✅ Session created: {session.session_id}")
    print(f"Status: {session.status}")
    
    if args.wait:
        print("Waiting for training to complete...")
        final_session = client.wait_for_session_completion(session.session_id)
        print(f"✅ Training completed with status: {final_session.status}")
    
    return 0


def cmd_test(client, args):
    """Handle test command."""
    csv_file = Path(args.csv_file)
    if not csv_file.exists():
        print(f"File not found: {csv_file}")
        return 1
    
    print(f"Testing predictions for session {args.session_id}...")
    
    results = client.test_csv_predictions(
        session_id=args.session_id,
        csv_file=str(csv_file),
        target_column=args.target_column,
        sample_size=args.sample_size
    )
    
    if results.get('accuracy_metrics'):
        metrics = results['accuracy_metrics']
        print(f"\n🎯 Results:")
        print(f"Accuracy: {metrics['accuracy']*100:.2f}%")
        print(f"Confidence: {metrics['average_confidence']*100:.2f}%")
        print(f"Correct: {metrics['correct_predictions']}/{metrics['total_predictions']}")
    else:
        print(f"✅ Predictions completed: {results['successful_predictions']} successful")
    
    return 0


def cmd_predict(client, args):
    """Handle predict command."""
    import json
    import pandas as pd
    from pathlib import Path
    
    input_path = Path(args.input)
    
    # Check if input is a CSV file
    if input_path.exists() and input_path.suffix.lower() == '.csv':
        print(f"📊 Loading CSV file: {input_path}")
        try:
            df = pd.read_csv(input_path)
            print(f"   Loaded {len(df)} records")
            
            # Sample records if requested (default is 1000, so only sample if explicitly set lower)
            if args.sample_size < len(df):
                df = df.sample(n=args.sample_size, random_state=42)
                print(f"   Sampling {len(df)} records for prediction")
            
            # Remove target column to avoid warnings
            target_column = 'Cancellation Non Renewal'
            if target_column in df.columns:
                df = df.drop(columns=[target_column])
                print(f"   Removed target column '{target_column}' from prediction data")
            
            print(f"\n🎯 Making predictions for {len(df)} records...")
            
            # Make individual predictions (simpler and more reliable)
            results = []
            for i, (_, row) in enumerate(df.iterrows()):
                record = row.to_dict()
                print(f"   Predicting record {i+1}/{len(df)}...", end=" ")
                
                try:
                    result = client.predict(args.session_id, record)
                    
                    # Extract prediction from response
                    if 'results' in result:
                        prediction = result['results']
                        # Get top prediction
                        predicted_class = max(prediction, key=prediction.get)
                        confidence = prediction[predicted_class]
                    elif 'metadata' in result:
                        # Use metadata if available (server already computed highest probability)
                        predicted_class = result['metadata'].get('predicted_class', 'Unknown')
                        confidence = result['metadata'].get('confidence', 0.0)
                        prediction = {predicted_class: confidence}
                    else:
                        raise ValueError("No prediction results found in response")
                    
                    results.append({
                        'record': i+1,
                        'prediction': predicted_class,
                        'confidence': confidence*100
                    })
                    
                    if args.verbose:
                        print(f"→ {predicted_class} ({confidence*100:.6f}%)")
                        print(f"   Full results: {prediction}")
                    else:
                        print(f"→ {predicted_class} ({confidence*100:.6f}%)")
                    
                except Exception as e:
                    print(f"❌ Error: {e}")
                    results.append({
                        'record': i+1,
                        'prediction': 'ERROR',
                        'confidence': 0
                    })
            
            # Summary
            print(f"\n📈 Prediction Summary:")
            successful = [r for r in results if r['prediction'] != 'ERROR']
            if successful:
                avg_confidence = sum(r['confidence'] for r in successful) / len(successful)
                print(f"   ✅ {len(successful)}/{len(results)} successful predictions")
                print(f"   📊 Average confidence: {avg_confidence:.6f}%")
                
                # Show prediction distribution
                from collections import Counter
                pred_counts = Counter(r['prediction'] for r in successful)
                print(f"   📋 Prediction distribution:")
                for pred, count in pred_counts.most_common():
                    pct = (count / len(successful)) * 100
                    print(f"      {pred}: {count} ({pct:.1f}%)")
                
                if args.verbose:
                    print(f"\n🔍 Full Results Structure:")
                    for result in successful:
                        print(f"   Record {result['record']}: {result}")
            
            return 0
            
        except Exception as e:
            print(f"❌ Error loading CSV: {e}")
            return 1
    
    # Handle JSON record
    try:
        record = json.loads(args.input)
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON record: {e}")
        print("💡 Tip: Use quotes around JSON: '{\"feature\": \"value\"}'")
        return 1
    
    print(f"🎯 Making prediction for session {args.session_id}...")
    
    try:
        result = client.predict(args.session_id, record)
        
        # Extract prediction from response
        if 'results' in result:
            prediction = result['results']
            
            print(f"\n🎯 Prediction:")
            for class_name, confidence in prediction.items():
                print(f"  {class_name}: {confidence*100:.2f}%")
            
            # Show top prediction
            predicted_class = max(prediction, key=prediction.get)
            confidence = prediction[predicted_class]
            print(f"\n→ Predicted: {predicted_class} ({confidence*100:.1f}% confidence)")
            
        elif 'metadata' in result:
            # Use metadata if available (server already computed highest probability)
            predicted_class = result['metadata'].get('predicted_class', 'Unknown')
            confidence = result['metadata'].get('confidence', 0.0)
            
            print(f"\n🎯 Prediction:")
            print(f"  {predicted_class}: {confidence*100:.2f}%")
            print(f"\n→ Predicted: {predicted_class} ({confidence*100:.1f}% confidence)")
            
        else:
            raise ValueError("No prediction results found in response")
        
        return 0
        
    except Exception as e:
        print(f"❌ Prediction failed: {e}")
        return 1


def cmd_status(client, args):
    """Handle status command."""
    print(f"Checking status for session {args.session_id}...")
    
    session_info = client.get_session_status(args.session_id)
    
    print(f"\n📊 Session Status:")
    print(f"ID: {session_info.session_id}")
    print(f"Type: {session_info.session_type}")
    print(f"Status: {session_info.status}")
    
    if session_info.jobs:
        print(f"\n🔧 Jobs:")
        for job_id, job in session_info.jobs.items():
            status = job.get('status', 'unknown')
            progress = job.get('progress')
            job_type = job.get('type', job_id.split('_')[0])
            
            # Build status line with progress and loss info
            status_line = f"  {job_type}: {status}"
            
            if progress is not None:
                # Fix percentage issue: show 100% when job is done
                progress_pct = 100.0 if status == 'done' else (progress * 100)
                status_line += f" ({progress_pct:.1f}%)"
            
            # Add training metrics for ES and Single Predictor jobs
            if job_type in ['train_es', 'train_single_predictor'] and status == 'running':
                metrics = []
                current_epoch = job.get('current_epoch')
                current_loss = job.get('current_loss')
                validation_loss = job.get('validation_loss')
                
                if current_epoch is not None:
                    metrics.append(f"Epoch {current_epoch}")
                if current_loss is not None:
                    metrics.append(f"Loss: {current_loss:.4f}")
                if validation_loss is not None:
                    metrics.append(f"Val Loss: {validation_loss:.4f}")
                
                if metrics:
                    status_line += f" - {', '.join(metrics)}"
            
            print(status_line)
    
    return 0


if __name__ == "__main__":
    sys.exit(main()) 