from pydantic import BaseModel, Field, NonNegativeInt, PrivateAttr


class CompilationMetadata(BaseModel):
    should_synthesize_separately: bool = Field(default=False)
    occurrences_number: NonNegativeInt = Field(default=1)
    _occupation_number: NonNegativeInt = PrivateAttr(default=0)
    disable_perm_check: bool = Field(default=False)
    disable_const_checks: list[str] | bool = Field(default=False)

    @property
    def occupation_number(self) -> NonNegativeInt:
        return self._occupation_number

    @occupation_number.setter
    def occupation_number(self, value: NonNegativeInt) -> None:
        self._occupation_number = value

    @property
    def has_user_directives(self) -> bool:
        return bool(self.disable_perm_check or self.disable_const_checks)

    def copy_user_directives(self) -> "CompilationMetadata":
        return CompilationMetadata(
            disable_perm_check=self.disable_perm_check,
            disable_const_checks=self.disable_const_checks,
        )
