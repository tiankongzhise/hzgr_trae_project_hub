from .workflow_processor import WorkFlowProcessor
from pathlib import Path






def main():
    rules_path = Path('data/工作流规则_1.xlsx')
    keywords_path = Path('data/待分类_1.xlsx')
    processor = WorkFlowProcessor()
    processor.process_workflow(rules_path,keywords_path)



if __name__ == '__main__':
    main()
