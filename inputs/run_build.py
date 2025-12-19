#!/usr/bin/env python3
import sys
import traceback
import build_ghg_and_merge

if __name__ == "__main__":
    try:
        sys.argv = [
            'build_ghg_and_merge.py',
            '--modelparams',
            'Polyester Modeling Parameters.xlsx',
            'Cotton Modeling Parameters.xlsx',
            'Nylon6 Parameters.xlsx',
            '--emission_factors_csv',
            'emission_factors_textile_industry.csv',
            '--mapping_csv',
            'material_substitution_mapping_pfmr2022.csv',
            '--out_impacts_csv',
            'material_impact_data.csv',
            '--out_merged_csv',
            'merged_material_recommendations.csv',
            '--out_details_dir',
            'mp_details'
        ]
        build_ghg_and_merge.main()
    except Exception as e:
        print("=" * 60)
        print("ERROR occurred:")
        print("=" * 60)
        traceback.print_exc()
        sys.exit(1)


