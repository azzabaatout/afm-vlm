from src.clip.image_utils import generate_image_metadata, load_images_from_path
from sentence_transformers import SentenceTransformer
from loguru import logger
from PIL import Image
import matplotlib.pyplot as plt
from torch.nn.functional import cosine_similarity
import numpy as np
import torch


class EmbeddingsModel:

    def __init__(self, model_name="paraphrase-multilingual-MiniLM-L12-v2"):
        self.text_embedder = SentenceTransformer(model_name)
        self.fig = plt.figure(figsize=(8, 20))
        self.dataset = None
        self.embeddings = None
        self.text_embeddings = None
        self.metadata = None
        self.img_paths = None
        self.images = None

    def text_to_embedding_transformer(text, model):
        return model.encode(text, convert_to_tensor=True)

    def load_and_process_dataset(self, image_paths):
        images = load_images_from_path(image_paths)
        return images

    def open_image(self, image_path):
        opened_image = Image.open(image_path)
        return opened_image

    def generate_dataset_metadata(self, image_paths):
        metadata = generate_image_metadata(image_paths)
        self.metadata = metadata
        logger.info(f"Metadata: {metadata}")
        return metadata

    def generate_dataset_embeddings_standard_tokenizer(self, text):
        model = self.text_embedder
        query_text_embedding = self.text_to_embedding_transformer(text, model)
        return query_text_embedding

    # search for similar images in database (delete duplicates? or keep them?)
    def search_similar_images(self, query):
        # Get text embeddings of class dataset
        text_embeddings = self.text_embeddings

        # Generate query text embeddings
        # query_text_embedding = self.process_and_embedd_query_text(query)
        model = self.text_embedder

        query_text_embedding = self.text_to_embedding_transformer(query, model)

        logger.info(f"Query text embedding shape: {query_text_embedding.shape}")
        logger.info(f"Text embeddings shape: {text_embeddings.shape}")

        # Compute cosine similarity between query text and all text embeddings
        similarities = cosine_similarity(query_text_embedding, text_embeddings, dim=1)

        # Find the index of the maximum similarity score
        max_similarity_index = torch.argmax(similarities).item()
        max_similarity = similarities[max_similarity_index].item()

        logger.info(f"Max similarity score: {max_similarity} at index: {max_similarity_index}")

        self.__display_similar_image(self.images[max_similarity_index])

    def __display_similar_image(self, similar_image):
        image = similar_image

        # Convert PIL image to NumPy array
        image_array = np.array(image)

        # Plot the image array using Matplotlib
        plt.imshow(image_array)
        plt.axis('off')  # Hide axis
        plt.show()

    def search_similar_images_top_3(self, query, gt):
        # text_embeddings = self.embeddings["text_embeds"]
        text_embeddings = self.text_embeddings

        # Generate query text embeddings
        model = self.text_embedder

        query_text_embedding = self.text_to_embedding_transformer(query, model)

        logger.info(f"Query text embedding shape: {query_text_embedding.shape}")
        logger.info(f"Text embeddings shape: {text_embeddings.shape}")

        # Compute cosine similarity between query text and all text embeddings
        similarities = cosine_similarity(query_text_embedding, text_embeddings, dim=1)

        indices = torch.topk(similarities, 3)

        logger.info(f"Top 3 Similarity scores: {indices} - GT is keyframe number {gt}")

        logger.info(f"Length of img paths: {len(self.img_paths)}")

        result = []

        for i in range(3):
            max_similarity_index = indices.indices[i].item()
            # print len of img paths
            if max_similarity_index <= len(self.img_paths):
                logger.info(f"#####GT is keyframe number {gt}#####")
                logger.info(
                    f"Max similarity for index {max_similarity_index} is the keyframe {self.img_paths[max_similarity_index]}")
                result.append(self.img_paths[max_similarity_index])
                # Can display the image since paths are faulty 'magic-rabbit'
                # opened_image = Image.open(self.img_paths[max_similarity_index])
                # self.__display_similar_image(opened_image)
            else:
                logger.info(f"Index {max_similarity_index} is out of range")

        return result

    def search_similar_images_top_10(self, query, gt):
        # text_embeddings = self.embeddings["text_embeds"]
        text_embeddings = self.text_embeddings

        # Generate query text embeddings
        model = self.text_embedder

        query_text_embedding = self.text_to_embedding_transformer(query, model)

        logger.info(f"Query text embedding shape: {query_text_embedding.shape}")
        logger.info(f"Text embeddings shape: {text_embeddings.shape}")

        # Compute cosine similarity between query text and all text embeddings
        similarities = cosine_similarity(query_text_embedding, text_embeddings, dim=1)

        indices = torch.topk(similarities, 3)

        logger.info(f"Top 3 Similarity scores: {indices} - GT is keyframe number {gt}")

        logger.info(f"Length of img paths: {len(self.img_paths)}")

        result = []

        for i in range(10):
            max_similarity_index = indices.indices[i].item()
            # print len of img paths
            if max_similarity_index <= len(self.img_paths):
                logger.info(f"#####GT is keyframe number {gt}#####")
                logger.info(
                    f"Max similarity for index {max_similarity_index} is the keyframe {self.img_paths[max_similarity_index]}")
                result.append(self.img_paths[max_similarity_index])
                # Can display the image since paths are faulty 'magic-rabbit'
                # opened_image = Image.open(self.img_paths[max_similarity_index])
                # self.__display_similar_image(opened_image)
            else:
                logger.info(f"Index {max_similarity_index} is out of range")

        return result
