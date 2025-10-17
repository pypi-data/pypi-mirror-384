from json import JSONEncoder
from typing import Any

from ninja.renderers import JSONRenderer
from ninja.responses import NinjaJSONEncoder

from biased.utils.default_json_encoder import DefaultJsonEncoder


class BiasedNinjaJsonEncoder(NinjaJSONEncoder):
    def default(self, o: Any) -> Any:
        try:
            return super().default(o)
        except TypeError:
            pass
        return DefaultJsonEncoder().default(o)


class BiasedNinjaJsonRenderer(JSONRenderer):
    encoder_class: type[JSONEncoder] = BiasedNinjaJsonEncoder
