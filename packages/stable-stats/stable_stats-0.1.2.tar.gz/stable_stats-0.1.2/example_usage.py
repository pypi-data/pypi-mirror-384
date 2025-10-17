"""
Example usage of the Stable package for beautifying statistical outputs.
"""

import numpy as np
from scipy import stats
import statsmodels.api as sm
from statsmodels.formula.api import ols
from stable import Stable

def main():
    # """Demonstrate various uses of the Stable package."""
    
    # print("=== Stable Package Examples ===\n")
    
    # # Example 1: Independent t-test
    # print("1. Independent t-test example:")
    # print("-" * 40)
    
    # Generate sample data
    np.random.seed(42)
    group1 = np.random.normal(100, 15, 30)  # Mean=100, SD=15, n=30
    group2 = np.random.normal(110, 15, 30)  # Mean=110, SD=15, n=30
    
    # Run t-test
    ttest_result = stats.ttest_ind(group1, group2)
    
    # Beautify with Stable
    stable_ttest = Stable(ttest_result)
    
    # print("Markdown output:")
    # print(stable_ttest.to_markdown(title="Independent t-test Results"))
    # print("\n" + "="*60 + "\n")
    
    # # Example 2: One-way ANOVA
    # print("2. One-way ANOVA example:")
    # print("-" * 40)
    
    # Generate sample data for 3 groups
    group_a = np.random.normal(50, 10, 25)
    group_b = np.random.normal(55, 10, 25)
    group_c = np.random.normal(60, 10, 25)
    
    # # Run ANOVA
    anova_result = stats.f_oneway(group_a, group_b, group_c)
    
    # Beautify with Stable
    stable_anova = Stable(anova_result)
    
    print("Markdown output:")
    print(stable_anova.to_markdown(title="One-way ANOVA Results"))
    print("\n" + "="*60 + "\n")
    
    # Example 3: Chi-square test
    print("3. Chi-square test example:")
    print("-" * 40)
    
    # Generate sample data
    observed = np.array([20, 30, 25, 25])  # Observed frequencies
    expected = np.array([25, 25, 25, 25])  # Expected frequencies
    
    # # Run chi-square test
    # chi2_result = stats.chisquare(observed, expected)
    
    # # Beautify with Stable
    # stable_chi2 = Stable(chi2_result)
    
    # print("Markdown output:")
    # print(stable_chi2.to_markdown(title="Chi-square Test Results"))
    # print("\n" + "="*60 + "\n")
    
    # # Example 4: Linear regression (statsmodels)
    # print("4. Linear regression example:")
    # print("-" * 40)
    
    # # Generate sample data
    # np.random.seed(42)
    # x = np.random.normal(0, 1, 100)
    # y = 2 * x + np.random.normal(0, 0.5, 100)
    
    # # Create DataFrame
    # import pandas as pd
    # df = pd.DataFrame({'x': x, 'y': y})
    
    # # Run regression
    # model = ols('y ~ x', data=df).fit()
    
    # # Beautify with Stable
    # stable_regression = Stable(model)
    
    # print("Markdown output:")
    # print(stable_regression.to_markdown(title="Linear Regression Results"))
    # print("\n" + "="*60 + "\n")
    
    # Example 5: Export to different formats
    print("5. Export to different formats:")
    print("-" * 40)
    
    # Use the t-test result from earlier
    print("HTML output (first 500 characters):")
    html_output = stable_ttest.to_html(title="T-test Results")
    print(html_output)
    print("\n")
    
    # # Export to Excel (commented out to avoid creating files in example)
    # stable_ttest.to_excel("ttest_results.xlsx")
    # print("Excel file created: ttest_results.xlsx")
    
    # # Get summary
    # print("Summary:")
    # print(stable_ttest.summary())
    # print("\n")
    
    # # Example 6: Using class methods for direct analysis
    # print("6. Using class methods for direct analysis:")
    # print("-" * 40)
    
    # # Direct t-test
    # stable_direct = Stable.from_ttest(group1, group2)
    # print("Direct t-test summary:")
    # print(stable_direct.summary())
    # print("\n")
    
    # # Direct ANOVA
    # stable_direct_anova = Stable.from_anova(group_a, group_b, group_c)
    # print("Direct ANOVA summary:")
    # print(stable_direct_anova.summary())
    # print("\n")
    
    # # Direct chi-square
    # stable_direct_chi2 = Stable.from_chi2(observed, expected)
    # print("Direct chi-square summary:")
    # print(stable_direct_chi2.summary())
    # print("\n")
    
    # print("=== Examples completed! ===")

if __name__ == "__main__":
    main()


