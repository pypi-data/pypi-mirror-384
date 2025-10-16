from annotated_dict import AnnotatedDict
from pandas import DataFrame


class Analytics(AnnotatedDict):
    row_count: int
    column_count: int
    column_names: list[str]
    bytes_value: int
    size_bytes: int
    size_kilobytes: float
    size_megabytes: float
    size_gigabytes: float

    @classmethod
    def from_dataframe(cls, df: DataFrame) -> 'Analytics':
        if not isinstance(df, DataFrame): raise TypeError(f"Expected DataFrame, got {type(df)} instead")
        bytes_value = int(df.memory_usage(deep=False).sum())
        return cls(**{
            "row_count": len(df),
            "column_count": len(df.columns),
            "column_names": list(df.columns),
            "size_bytes": bytes_value,
            "size_kilobytes": round(bytes_value / 1024, 2),
            "size_megabytes": round(bytes_value / (1024 ** 2), 2),
            "size_gigabytes": round(bytes_value / (1024 ** 3), 6)
        })

    @classmethod
    def compare_schema(cls, df1, df2):
        if not isinstance(df1, DataFrame) or not isinstance(df2, DataFrame):
            raise TypeError(f"Expected DataFrame, got {type(df1)} or {type(df2)} instead")

        analytics1 = cls.from_dataframe(df1)
        analytics2 = cls.from_dataframe(df2)

        set1 = set(analytics1.column_names)
        set2 = set(analytics2.column_names)

        only_in_df1 = list(set1 - set2)
        only_in_df2 = list(set2 - set1)

        return {
            "is_different": len(only_in_df1) > 0 or len(only_in_df2) > 0,
            "column_count_difference": analytics1.column_count - analytics2.column_count,
            "only_in_df1": only_in_df1,
            "only_in_df2": only_in_df2,
            "common_columns": list(set1 & set2),
            "all_differences": list(set1.symmetric_difference(set2))
        }
