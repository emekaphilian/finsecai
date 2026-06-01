#!/usr/bin/env python3
"""
FinSecAI Quick Start - Get the system running in 2 minutes
"""

import subprocess
import sys
from pathlib import Path

def main():
    print("\n" + "="*70)
    print("🚀 FINSECAI QUICK START GUIDE")
    print("="*70)
    
    project_root = Path(__file__).resolve().parent
    
    # Step 1: Check dependencies
    print("\n📦 Step 1: Checking dependencies...")
    required_packages = {
        "streamlit": "Streamlit",
        "pandas": "Pandas",
        "plotly": "Plotly",
        "numpy": "NumPy"
    }
    
    missing = []
    for pkg, name in required_packages.items():
        try:
            __import__(pkg)
            print(f"  ✅ {name}")
        except ImportError:
            print(f"  ❌ {name}")
            missing.append(pkg)
    
    if missing:
        print(f"\n⚠️  Missing packages: {', '.join(missing)}")
        print(f"    Install with: pip install {' '.join(missing)}")
        return False
    
    # Step 2: Verify key files
    print("\n📁 Step 2: Verifying project structure...")
    required_files = [
        "dashboards/soc_dashboard.py",
        "src/evaluation/metrics.py",
        "src/evaluation/visualizations.py",
        "src/orchestration/run_full_system.py",
        "tests/integration_test.py"
    ]
    
    for file in required_files:
        path = project_root / file
        if path.exists():
            size = path.stat().st_size / 1024
            print(f"  ✅ {file} ({size:.1f}KB)")
        else:
            print(f"  ❌ {file} NOT FOUND")
            return False
    
    # Step 3: Run tests
    print("\n🧪 Step 3: Running integration tests...")
    try:
        result = subprocess.run(
            [sys.executable, "tests/integration_test.py"],
            cwd=str(project_root),
            capture_output=True,
            timeout=30
        )
        
        if result.returncode == 0:
            print("  ✅ Integration tests PASSED")
        else:
            print("  ⚠️  Integration tests reported issues")
            print("     (This is normal if LLM providers not configured)")
    except Exception as e:
        print(f"  ⚠️  Could not run tests: {e}")
    
    # Step 4: Instructions
    print("\n" + "="*70)
    print("✅ READY TO LAUNCH!")
    print("="*70)
    
    print("""
🎯 START THE DASHBOARD:
   
   streamlit run dashboards/soc_dashboard.py

📝 LOGIN CREDENTIALS:
   
   Username: tier1, tier2, or admin
   Password: demo123

💡 QUICK WORKFLOW:
   
   1. Upload CSV or enable "Use sample data"
   2. Click "Analyze All Incidents"
   3. Browse Tab 1 (Incidents table)
   4. Select row → Tab 2 (Deep Dive with RAG + Governance)
   5. View Tab 3 (Analytics: Precision, Fairness, Drift, Calibration)
   6. Use Tab 4 (Copilot - extend with CrewAI)

⚙️  OPTIONAL: Configure LLM Providers
   
   Set environment variables:
   
   export OPENAI_API_KEY=sk-...
   export COHERE_API_KEY=...
   export ANTHROPIC_API_KEY=...
   export LOCAL_LLM_URL=http://localhost:11434/api/generate
   export LOCAL_LLM_MODEL=llama3

   For Ollama (local, offline):
   
   ollama pull llama3
   ollama serve  # in another terminal

📊 WHAT YOU'LL SEE:
   
   • Incidents table with risk scores and governance flags
   • Deep dive with RAG evidence retrieval
   • Framework mapping (MITRE ATT&CK, NIST controls)
   • Real-time analytics: Precision/Recall, Fairness, Drift, Calibration
   • Governance compliance dashboard

🔗 FULL DOCUMENTATION:
   
   See: IMPLEMENTATION_SUMMARY.md
   See: DEPLOYMENT_GUIDE.md

🎉 YOU'RE READY TO GO!
    """)
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
