from src.kw_cf import models





def test():
    x = models.StageSaveResult(stage=1, status='success',file_path={},next_stage=3)
    return x


if __name__ == '__main__':
    print(test())