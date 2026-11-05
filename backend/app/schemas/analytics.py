from pydantic import BaseModel


class BlockStudentCount(BaseModel):
    block_name: str
    student_count: int


class PassFailCount(BaseModel):
    final_status: str
    count: int


class HouseStudentCount(BaseModel):
    house_name: str
    student_count: int


class LatestYearSummary(BaseModel):
    year_label: str
    students_by_block: list[BlockStudentCount]
    pass_fail: list[PassFailCount]
    students_by_house: list[HouseStudentCount]