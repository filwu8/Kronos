import os
import torch
print('torch=', torch.__version__)
print('torch.version.cuda=', getattr(torch.version, 'cuda', None))
print('is_available=', torch.cuda.is_available())
print('CUDA_VISIBLE_DEVICES=', os.getenv('CUDA_VISIBLE_DEVICES'))
if torch.cuda.is_available():
    print('device=', torch.cuda.get_device_name(0))

