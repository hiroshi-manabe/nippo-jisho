#!/usr/bin/env python3
"""Calamari training with recognition-preserving Roman/italic initialization.

Uses the installed Calamari trainer unchanged except for its output-layer
warmstart. Do not edit installed packages. Run in the Calamari environment.
"""
from collections import Counter
import math
import numpy as np

OFFSET=0xF0000


def base_character(char):
    return chr(ord(char)-OFFSET) if char and OFFSET<=ord(char)<OFFSET+0xFFFE else char


def duplicate_logits(old_kernel,old_bias,new_kernel,new_bias,old_charset,new_charset):
    """Calamari stores nonblank symbols first and the CTC blank last."""
    assert old_charset[0]==new_charset[0]==''
    kernel,bias=new_kernel.copy(),new_bias.copy()
    old={c:i for i,c in enumerate(old_charset[1:])}
    counts=Counter(base_character(c) for c in new_charset[1:])
    copied=0
    for j,c in enumerate(new_charset[1:]):
        base=base_character(c)
        if base in old:
            kernel[:,j]=old_kernel[:,old[base]]
            bias[j]=old_bias[old[base]]-math.log(counts[base])
            copied+=1
    return kernel,bias,copied


def main():
    from calamari_ocr.ocr.training.trainer import Trainer
    from calamari_ocr.ocr.training.warmstart import WarmStarterWithCodecAdaption
    from calamari_ocr.scripts.train import run

    class StyledWarmStarter(WarmStarterWithCodecAdaption):
        def copy_weights_from_model(self,target_model,weights,indices_to_delete,indices_to_add):
            super().copy_weights_from_model(target_model,weights,indices_to_delete,indices_to_add)
            pairs=[(t,s) for t,s in zip(target_model.weights,weights) if 'logits' in t.name]
            target_kernel,source_kernel=next((t,s) for t,s in pairs if 'kernel' in t.name)
            target_bias,source_bias=next((t,s) for t,s in pairs if 'bias' in t.name)
            kernel,bias,copied=duplicate_logits(source_kernel,source_bias,
                target_kernel.numpy(),target_bias.numpy(),self.old_charset,self.new_charset)
            target_kernel.assign(kernel)
            target_bias.assign(bias)
            print(f'Style warmstart: copied {copied} character/style outputs; blank and unknown characters unchanged',flush=True)

    def create(self):
        result=StyledWarmStarter(self.params.warmstart,codec_changes=self._codec_changes)
        result.old_charset=self.checkpoint.dict['scenario']['data']['codec']['charset']
        result.new_charset=self._data.params.codec.charset
        return result

    Trainer.create_warmstarter=create
    run()


if __name__=='__main__':
    main()
