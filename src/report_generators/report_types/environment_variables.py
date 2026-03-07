"""
Environment Variables Report
Shows HC_ environment variables usage across Groovy scripts, JavaScript, and XSLTs
"""

from typing import Dict, Any, List
from ..base_report import BaseReport
from utils.logger import get_logger

logger = get_logger(__name__)


class EnvironmentVariablesReport(BaseReport):
    """Generates environment variables usage report"""
    
    def get_report_name(self) -> str:
        return "environment_variables"
    
    def get_report_title(self) -> str:
        return "Environment Variables Usage (HC_ Variables)"
    
    def generate(self) -> Dict[str, Any]:
        """Generate environment variables usage data"""
        logger.info("Generating Environment Variables report...")
        
        # Query environment variable data
        query = """
        SELECT 
            ev.packageId as package_id,
            ev.parentType as parent_type,
            ev.parentName as parent_name,
            ev.fileName as file_name,
            ev.fileType as file_type,
            ev.envVariableCount as var_count,
            ev.envVariableList as var_list
        FROM environment_variable_check ev
        WHERE ev.tenant_id = ?
        ORDER BY ev.parentType, ev.parentName, ev.fileName
        """
        
        env_vars = self.execute_query(query, (self.tenant_id,))
        
        # Process data and collect statistics
        report_data = []
        stats = {
            'total_files': 0,
            'total_variables': 0,
            'unique_variables': set(),
            'by_parent_type': {},
            'by_file_type': {},
            'most_used_vars': {}
        }
        
        for row in env_vars:
            stats['total_files'] += 1
            var_count = self.safe_int(row.get('var_count', 0))
            stats['total_variables'] += var_count
            
            # Track by parent type
            parent_type = row.get('parent_type', 'Unknown')
            stats['by_parent_type'][parent_type] = stats['by_parent_type'].get(parent_type, 0) + 1
            
            # Track by file type
            file_type = row.get('file_type', 'Unknown')
            stats['by_file_type'][file_type] = stats['by_file_type'].get(file_type, 0) + 1
            
            # Process variable list
            var_list = row.get('var_list', '').split('|') if row.get('var_list') else []
            for var in var_list:
                if var:
                    stats['unique_variables'].add(var)
                    stats['most_used_vars'][var] = stats['most_used_vars'].get(var, 0) + 1
            
            report_data.append({
                'package_id': row.get('package_id', 'N/A'),
                'parent_type': parent_type,
                'parent_name': row.get('parent_name', 'N/A'),
                'file_name': row.get('file_name', 'N/A'),
                'file_type': file_type,
                'var_count': var_count,
                'variables': ', '.join(var_list) if var_list else 'N/A'
            })
        
        # Get top 10 most used variables
        top_vars = sorted(stats['most_used_vars'].items(), key=lambda x: x[1], reverse=True)[:10]
        
        stats['unique_variables_count'] = len(stats['unique_variables'])
        stats['top_variables'] = [{'name': var, 'count': count} for var, count in top_vars]
        
        # Remove set from stats (not JSON serializable)
        del stats['unique_variables']
        
        self.report_data = {
            'env_vars': report_data,
            'stats': stats,
            'columns': [
                {'key': 'parent_type', 'label': 'Parent Type', 'sortable': True},
                {'key': 'parent_name', 'label': 'Parent Name', 'sortable': True},
                {'key': 'file_name', 'label': 'File Name', 'sortable': True},
                {'key': 'file_type', 'label': 'File Type', 'sortable': True},
                {'key': 'var_count', 'label': 'Variable Count', 'sortable': True},
                {'key': 'variables', 'label': 'Variables', 'sortable': False}
            ]
        }
        
        logger.info(f"  Found {stats['total_files']} files with environment variables")
        logger.info(f"  Total unique variables: {stats['unique_variables_count']}")
        
        return self.report_data
    
    def get_summary_metrics(self) -> Dict[str, Any]:
        """Get summary metrics for dashboard"""
        if not self.report_data:
            self.generate()
        
        stats = self.report_data.get('stats', {})
        return {
            'total_env_var_files': stats.get('total_files', 0),
            'unique_env_variables': stats.get('unique_variables_count', 0)
        }
    
    def get_chart_data(self) -> List[Dict[str, Any]]:
        """Get chart data for visualization"""
        if not self.report_data:
            self.generate()
        
        stats = self.report_data.get('stats', {})
        
        charts = []
        
        # Chart 1: Files by parent type
        by_parent = stats.get('by_parent_type', {})
        if by_parent:
            charts.append({
                'chart_id': 'env_vars_by_parent',
                'chart_type': 'pie',
                'title': 'Files by Parent Type',
                'data': {
                    'labels': list(by_parent.keys()),
                    'values': list(by_parent.values()),
                    'colors': ['#007bff', '#28a745', '#ffc107']
                }
            })
        
        # Chart 2: Top 10 most used variables
        top_vars = stats.get('top_variables', [])[:10]
        if top_vars:
            charts.append({
                'chart_id': 'top_env_vars',
                'chart_type': 'bar',
                'title': 'Top 10 Most Used Variables',
                'data': {
                    'labels': [v['name'] for v in top_vars],
                    'values': [v['count'] for v in top_vars],
                    'color': '#17a2b8'
                }
            })
        
        return charts