#!/usr/bin/env python3
"""
Generate all test fixtures for the marking system.

This script creates realistic test data including notebooks, rubrics,
API mocks, and expected Excel outputs.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def generate_fixtures():
    """Generate all test fixtures."""
    try:
        print("🔧 Generating Test Fixtures")
        print("=" * 40)
        
        # Import fixture generators
        from tests.fixtures.generate_fixtures import FixtureCoordinator
        
        # Create coordinator
        coordinator = FixtureCoordinator()
        
        print("📁 Creating fixture directories...")
        coordinator.fixtures_dir.mkdir(parents=True, exist_ok=True)
        
        print("📝 Generating all fixtures...")
        coordinator.generate_all_fixtures()
        
        print("✅ All fixtures generated successfully!")
        print(f"📂 Fixtures saved to: {coordinator.fixtures_dir}")
        
        # List what was created
        fixtures_created = []
        if (coordinator.fixtures_dir / "notebooks").exists():
            notebook_files = list((coordinator.fixtures_dir / "notebooks").glob("*.ipynb"))
            fixtures_created.extend([f"📓 {f.name}" for f in notebook_files])
        
        if (coordinator.fixtures_dir / "rubrics").exists():
            rubric_files = list((coordinator.fixtures_dir / "rubrics").glob("*.csv"))
            fixtures_created.extend([f"📋 {f.name}" for f in rubric_files])
        
        if (coordinator.fixtures_dir / "api_mocks").exists():
            api_files = list((coordinator.fixtures_dir / "api_mocks").glob("*.json"))
            fixtures_created.extend([f"🔌 {f.name}" for f in api_files])
        
        if (coordinator.fixtures_dir / "excel_outputs").exists():
            excel_files = list((coordinator.fixtures_dir / "excel_outputs").glob("*.xlsx"))
            fixtures_created.extend([f"📊 {f.name}" for f in excel_files])
        
        if fixtures_created:
            print("\n📦 Fixtures created:")
            for fixture in fixtures_created[:10]:  # Show first 10
                print(f"   {fixture}")
            if len(fixtures_created) > 10:
                print(f"   ... and {len(fixtures_created) - 10} more files")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Make sure all fixture generator modules are available")
        return False
    except Exception as e:
        print(f"❌ Error generating fixtures: {e}")
        import traceback
        traceback.print_exc()
        return False

def clean_fixtures():
    """Clean up existing fixtures."""
    fixtures_dir = Path("tests/fixtures")
    
    dirs_to_clean = [
        fixtures_dir / "notebooks",
        fixtures_dir / "rubrics", 
        fixtures_dir / "api_mocks",
        fixtures_dir / "excel_outputs"
    ]
    
    print("🧹 Cleaning existing fixtures...")
    for dir_path in dirs_to_clean:
        if dir_path.exists():
            import shutil
            shutil.rmtree(dir_path)
            print(f"   Removed: {dir_path}")

def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate test fixtures for marking system")
    parser.add_argument("--clean", action="store_true", help="Clean existing fixtures first")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be generated without creating files")
    
    args = parser.parse_args()
    
    print("🎯 Test Fixture Generator")
    print("=" * 50)
    
    if args.clean:
        clean_fixtures()
        print()
    
    if args.dry_run:
        print("🔍 Dry run mode - showing what would be generated:")
        print("   📓 Notebooks: perfect_student.ipynb, missing_tasks_student.ipynb, ...")
        print("   📋 Rubrics: standard_rubric.csv, invalid_rubric.csv, ...")
        print("   🔌 API Mocks: perfect_responses.json, error_responses.json, ...")
        print("   📊 Excel Outputs: perfect_student_marks.xlsx, ...")
        print("✅ Dry run completed")
        return
    
    success = generate_fixtures()
    
    if success:
        print("\n🎉 Fixture generation completed successfully!")
        print("\n📝 Next steps:")
        print("   1. Run: pytest tests/test_integration_focused.py -v")
        print("   2. Or run: python run_integration_tests.py")
    else:
        print("\n❌ Fixture generation failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
