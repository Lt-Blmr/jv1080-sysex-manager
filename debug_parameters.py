#!/usr/bin/env python3

from jv1080_manager import JV1080Manager

# Create manager and check what parameters are available
manager = JV1080Manager()

print("Available parameter groups:")
groups = manager.list_parameter_groups()
for group in groups:
    print(f"  - {group}")

print(f"\nParameters in 'temp_performance_common':")
params = manager.list_parameters('temp_performance_common')
for i, param in enumerate(params):
    print(f"  {i+1:2d}. {param}")

print(f"\nTotal parameters: {len(params)}")

# Check if EFX:Type is in there
if 'EFX:Type' in params:
    print("\n✅ EFX:Type found!")
else:
    print("\n❌ EFX:Type NOT found!")
    # Show which params contain 'EFX'
    efx_params = [p for p in params if 'EFX' in p]
    if efx_params:
        print("EFX-related parameters found:")
        for p in efx_params:
            print(f"  - {p}")
