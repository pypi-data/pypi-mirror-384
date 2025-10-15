class TrainParams:
    def __init__(self, id, algorithm, dataset_id, epoch, batch_size, split_ratio):
        self.id = id
        self.algorithm = algorithm
        self.dataset_id = dataset_id
        self.epoch = epoch
        self.batch_size = batch_size
        self.split_ratio = split_ratio

    def __repr__(self):
        return f"TrainParams(id={self.id}, algorithm={self.algorithm}, " \
               f"dataset_id={self.dataset_id}, epoch={self.epoch}, batch_size={self.batch_size}, " \
               f"split_ratio={self.split_ratio})"