import abc

from langchain_community.embeddings import XinferenceEmbeddings


class EmbeddingFactoryBase:
    provider: str

    @classmethod
    @abc.abstractmethod
    def create_embedding(cls, base_url: str, model_uid: str, api_key: str = '', dims: int = 1024):
        raise NotImplemented


class XinferenceEmbeddingFactory(EmbeddingFactoryBase):
    provider: str = 'xinference'

    @classmethod
    def create_embedding(cls, base_url: str, model_uid: str, api_key: str = '', dims: int = 1024):
        # assert embedding_server_url is not None and embedding_server_url != ''
        # assert embedding_model_uid is not None and embedding_model_uid != ''
        embedding = XinferenceEmbeddings(
            server_url=base_url,
            model_uid=model_uid,  # replace model_uid with the model UID return from launching the model
        )
        return embedding


_FACTORY_LIST = [
    XinferenceEmbeddingFactory
]


class EmbeddingFactory:
    @classmethod
    def create_embedding(cls, base_url: str, model_uid: str, api_key: str = '', dims: int = 1024, provider: str = 'xinference'):
        for factory in _FACTORY_LIST:
            if factory.provider == provider:
                return factory.create_embedding(base_url=base_url, model_uid=model_uid, api_key=api_key, dims=dims)
        raise Exception(f'不支持的embedding provider配置: [{provider}]')
