class GroupedRow:
    def __init__(
        self,
        customer: str,
        service: str,
        description: str,
        rate: float,
        processing_fee: bool,
        manager: str,
        row_index_start: int,
        service_type: str = "",
    ):
        self.customer: str = customer
        self.service: str = service
        self.description: str = description
        self.rate: float = rate
        self.processing_fee: bool = processing_fee
        self.manager: str = manager
        self.row_index_start: int = row_index_start
        self.service_type: str = service_type
