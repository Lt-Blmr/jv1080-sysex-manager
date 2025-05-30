#!/usr/bin/env python3
"""
JV-1080 Expansion Card SysEx Analyzer
Focused analysis of Vintage and Techno expansion card SysEx files to validate parser functionality.
"""

import logging
from pathlib import Path
from typing import Dict, List, Any
import sys
from collections import defaultdict, Counter

from sysex_parser import SysExParser, ParsedParameter, ParsedPreset

# Configure detailed logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('expansion_card_analysis.log')
    ]
)
logger = logging.getLogger(__name__)

class ExpansionCardAnalyzer:
    """Analyzer for JV-1080 expansion card SysEx files."""
    
    def __init__(self):
        self.parser = SysExParser()
        self.results = {}
    
    def analyze_file(self, file_path: Path) -> Dict[str, Any]:
        """Analyze a single SysEx file and return detailed information."""
        logger.info(f"[ANALYZING] {file_path.name}")
        
        try:
            # Parse the file
            parameters = self.parser.parse_sysex_file(str(file_path))
            
            # Get file size info
            file_size = file_path.stat().st_size
            
            # Group parameters by type
            grouped_params = self.parser.group_parameters_by_type(parameters)
            
            # Analyze parameter distribution
            param_groups = Counter(param.group_name for param in parameters)
            unique_addresses = len(set(tuple(param.address) for param in parameters))
            
            # Create analysis result
            analysis = {
                'file_name': file_path.name,
                'file_size_bytes': file_size,
                'total_parameters': len(parameters),
                'unique_addresses': unique_addresses,
                'parameter_groups': dict(param_groups),
                'grouped_parameters': grouped_params,
                'raw_parameters': parameters
            }
            
            # Detect card type and banks
            card_info = self._detect_card_type(parameters, file_path.name)
            analysis.update(card_info)
            
            logger.info(f"[SUCCESS] {file_path.name}: {len(parameters)} parameters, {len(param_groups)} groups")
            return analysis
            
        except Exception as e:
            logger.error(f"[ERROR] Error analyzing {file_path.name}: {e}")
            return {
                'file_name': file_path.name,
                'error': str(e),
                'total_parameters': 0
            }
    
    def _detect_card_type(self, parameters: List[ParsedParameter], filename: str) -> Dict[str, Any]:
        """Detect what type of card data this is (Performance, Patch, Rhythm)."""
        
        # Analyze address patterns to determine bank types
        addresses = [tuple(param.address) for param in parameters]
        address_patterns = Counter(addresses)
        
        # JV-1080 address mapping (based on manual)
        bank_types = {
            'performance': [],
            'patch': [],
            'rhythm': [],
            'unknown': []
        }
        
        for addr in addresses:
            addr_hex = [f"{x:02X}" for x in addr]
            addr_str = " ".join(addr_hex)
            
            # Performance banks typically start with 01 xx xx
            if addr[0] == 0x01:
                bank_types['performance'].append(addr)
            # Patch banks typically start with 02 xx xx or 03 xx xx  
            elif addr[0] in [0x02, 0x03]:
                bank_types['patch'].append(addr)
            # Rhythm banks typically start with 04 xx xx
            elif addr[0] == 0x04:
                bank_types['rhythm'].append(addr)
            else:
                bank_types['unknown'].append(addr)
        
        # Count unique addresses by type
        detected_banks = {}
        for bank_type, addrs in bank_types.items():
            if addrs:
                detected_banks[bank_type] = len(set(addrs))
        
        # Determine primary card type
        if detected_banks:
            primary_type = max(detected_banks.keys(), key=lambda k: detected_banks[k])
        else:
            primary_type = 'unknown'
        
        return {
            'detected_card_type': primary_type,
            'detected_banks': detected_banks,
            'bank_distribution': {k: len(v) for k, v in bank_types.items() if v}
        }
    
    def analyze_vintage_and_techno_cards(self) -> Dict[str, Any]:
        """Analyze the Vintage and Techno expansion card files."""
        
        sysex_dir = Path("sysex_files")
        target_files = [
            "Vintage1.syx",
            "Vintage2.syx", 
            "Techno1.syx",
            "Techno2.syx"
        ]
        
        logger.info("[EXPANSION CARD ANALYSIS] Starting Vintage & Techno Expansion Card Analysis")
        logger.info("=" * 60)
        
        results = {}
        
        for filename in target_files:
            file_path = sysex_dir / filename
            if file_path.exists():
                results[filename] = self.analyze_file(file_path)
            else:
                logger.warning(f"[WARNING] File not found: {filename}")
                results[filename] = {'error': 'File not found'}
        
        # Generate summary report
        self._generate_summary_report(results)
        
        return results
    
    def _generate_summary_report(self, results: Dict[str, Any]) -> None:
        """Generate a comprehensive summary report."""
        
        logger.info("\n" + "=" * 60)
        logger.info("[SUMMARY] EXPANSION CARD ANALYSIS SUMMARY")
        logger.info("=" * 60)
        
        total_params = 0
        total_files = 0
        card_types = Counter()
        
        for filename, analysis in results.items():
            if 'error' not in analysis:
                total_files += 1
                total_params += analysis['total_parameters']
                card_types[analysis.get('detected_card_type', 'unknown')] += 1
                
                logger.info(f"\n[FILE] {filename}:")
                logger.info(f"   Size: {analysis['file_size_bytes']:,} bytes")
                logger.info(f"   Parameters: {analysis['total_parameters']}")
                logger.info(f"   Unique Addresses: {analysis['unique_addresses']}")
                logger.info(f"   Detected Type: {analysis.get('detected_card_type', 'unknown')}")
                
                if 'detected_banks' in analysis:
                    logger.info(f"   Banks Found: {analysis['detected_banks']}")
                
                if 'parameter_groups' in analysis:
                    logger.info(f"   Parameter Groups: {analysis['parameter_groups']}")
        
        logger.info(f"\n[TOTALS]:")
        logger.info(f"   Files Analyzed: {total_files}")
        logger.info(f"   Total Parameters: {total_params}")
        logger.info(f"   Card Types: {dict(card_types)}")
        
        # Save detailed results
        self._save_detailed_results(results)
    
    def _save_detailed_results(self, results: Dict[str, Any]) -> None:
        """Save detailed analysis results to files."""
        
        import json
        
        # Save JSON report
        output_dir = Path("presets") / "analysis"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        json_file = output_dir / "expansion_card_analysis.json"
        
        # Prepare JSON-serializable data
        json_results = {}
        for filename, analysis in results.items():
            json_data = analysis.copy()
            
            # Remove non-serializable objects
            if 'raw_parameters' in json_data:
                del json_data['raw_parameters']
            if 'grouped_parameters' in json_data:
                del json_data['grouped_parameters']
                
            json_results[filename] = json_data
        
        with open(json_file, 'w') as f:
            json.dump(json_results, f, indent=2)
        
        logger.info(f"[SAVED] Detailed results saved to: {json_file}")
        
        # Save parameter details
        self._save_parameter_details(results, output_dir)
    
    def _save_parameter_details(self, results: Dict[str, Any], output_dir: Path) -> None:
        """Save detailed parameter information for each file."""
        
        for filename, analysis in results.items():
            if 'raw_parameters' in analysis:
                param_file = output_dir / f"{Path(filename).stem}_parameters.txt"
                
                with open(param_file, 'w') as f:
                    f.write(f"Parameter Analysis for {filename}\n")
                    f.write("=" * 50 + "\n\n")
                    
                    for i, param in enumerate(analysis['raw_parameters']):
                        f.write(f"Parameter {i+1}:\n")
                        f.write(f"  Group: {param.group_name}\n")
                        f.write(f"  Name: {param.parameter_name}\n")
                        f.write(f"  Value: {param.value}\n")
                        f.write(f"  Address: {[f'{x:02X}' for x in param.address]}\n")
                        f.write(f"  Raw Message: {[f'{x:02X}' for x in param.raw_message]}\n")
                        f.write("\n")
                
                logger.info(f"[SAVED] Parameter details saved: {param_file}")

def main():
    """Main function to run the expansion card analysis."""
    
    analyzer = ExpansionCardAnalyzer()
    
    try:
        # Analyze Vintage and Techno cards
        results = analyzer.analyze_vintage_and_techno_cards()
        
        # Validate parser functionality
        logger.info("\n" + "=" * 60)
        logger.info("[VALIDATION] PARSER VALIDATION")
        logger.info("=" * 60)
        
        validation_passed = True
        
        for filename, analysis in results.items():
            if 'error' in analysis:
                logger.error(f"[FAILED] {filename}: {analysis['error']}")
                validation_passed = False
            elif analysis['total_parameters'] == 0:
                logger.warning(f"[WARNING] {filename}: No parameters parsed")
                validation_passed = False
            else:
                logger.info(f"[PASSED] {filename}: Successfully parsed {analysis['total_parameters']} parameters")
        
        if validation_passed:
            logger.info("\n[SUCCESS] Parser validation PASSED - All files processed successfully!")
        else:
            logger.error("\n[FAILED] Parser validation FAILED - Some issues detected")
            
        return validation_passed
        
    except Exception as e:
        logger.error(f"[CRITICAL] Analysis failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
