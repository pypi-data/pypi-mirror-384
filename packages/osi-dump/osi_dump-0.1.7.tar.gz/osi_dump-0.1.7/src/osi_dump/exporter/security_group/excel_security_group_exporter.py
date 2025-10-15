import logging
import pandas as pd
from typing import Generator
from osi_dump import util
from osi_dump.exporter.security_group.security_group_exporter import SecurityGroupExporter
from osi_dump.model.security_group import SecurityGroup

logger = logging.getLogger(__name__)

class ExcelSecurityGroupExporter(SecurityGroupExporter):
    def __init__(self, sheet_name: str, output_file: str):
        self.sheet_name = sheet_name
        self.output_file = output_file

    def export_security_groups(self, security_groups: Generator[SecurityGroup, None, None]):
        
        data_generator = (sg.model_dump() for sg in security_groups)

        df = pd.json_normalize(
            data_generator,
            record_path='rules',
            meta=['security_group_id', 'name', 'project_id', 'description'],
            record_prefix='rule.'
        )

        if df.empty:
            logger.info(f"No security groups to export for {self.sheet_name}")
            return
            
        logger.info(f"Exporting security groups for {self.sheet_name}")
        try:
            util.export_data_excel(self.output_file, sheet_name=self.sheet_name, df=df)
            logger.info(f"Exported security groups for {self.sheet_name}")
        except Exception as e:
            logger.warning(f"Exporting security groups for {self.sheet_name} error: {e}")