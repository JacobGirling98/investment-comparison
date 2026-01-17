import os
from src.adapters.pdf_plumber_extractor import PdfPlumberExtractor
from src.adapters.moneyfarm_reader import MoneyfarmReader
from src.adapters.interactive_investor_reader import InteractiveInvestorReader
from src.adapters.matplotlib_chart_generator import MatplotlibChartGenerator
from src.domain.service import PerformanceService

def main():
    extractor = PdfPlumberExtractor()
    performance_service = PerformanceService()
    chart_generator = MatplotlibChartGenerator()
    
    # Readers
    moneyfarm_reader = MoneyfarmReader(extractor)
    ii_reader = InteractiveInvestorReader(extractor)
    
    print("Reading statements...")
    
    # Directories
    mf_dir = "statements/moneyfarm"
    ii_dir = "statements/interactive-investor"
    
    mf_portfolio = moneyfarm_reader.read_all(mf_dir)
    ii_portfolio = ii_reader.read_all(ii_dir)
    
    # Calculate Returns (XIRR)
    mf_xirr = performance_service.calculate_xirr(mf_portfolio)
    ii_xirr = performance_service.calculate_xirr(ii_portfolio)
    
    # Calculate Returns (Simple)
    mf_simple = performance_service.calculate_total_return(mf_portfolio)
    ii_simple = performance_service.calculate_total_return(ii_portfolio)
    
    results = {
        "Moneyfarm": (mf_xirr, mf_simple),
        "Interactive Investor": (ii_xirr, ii_simple)
    }
    
    print("\n--- Results ---")
    print(f"{ 'Account':<25} | {'Annualized (XIRR)':<20} | {'Total Return (Simple)':<20}")
    print("-" * 70)
    for name, (xirr, simple) in results.items():
        print(f"{name:<25} | {xirr*100:>18.2f}% | {simple*100:>18.2f}%")
    
    # Generate Chart
    chart_path = "performance_comparison.png"
    chart_generator.generate_performance_chart(results, chart_path)
    print(f"\nChart saved to {chart_path}")

if __name__ == "__main__":
    main()