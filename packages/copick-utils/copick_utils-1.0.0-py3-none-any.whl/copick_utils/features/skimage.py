import numpy as np
import zarr
from numcodecs import Blosc
from skimage.feature import multiscale_basic_features


def compute_skimage_features(
    tomogram,
    feature_type,
    copick_root,
    intensity=True,
    edges=True,
    texture=True,
    sigma_min=0.5,
    sigma_max=16.0,
    feature_chunk_size=None,
):
    """
    Processes the tomogram chunkwise and computes the multiscale basic features.
    Allows for optional feature chunk size.
    """
    image = zarr.open(tomogram.zarr(), mode="r")["0"]
    input_chunk_size = feature_chunk_size if feature_chunk_size else image.chunks
    chunk_size = input_chunk_size if len(input_chunk_size) == 3 else input_chunk_size[1:]

    overlap = int(chunk_size[0] / 2)

    print(f"Processing image with shape {image.shape}")
    print(f"Using chunk size: {chunk_size}, overlap: {overlap}")

    # Determine number of features by running on a small test array
    test_chunk = np.zeros((10, 10, 10), dtype=image.dtype)
    test_features = multiscale_basic_features(
        test_chunk,
        intensity=intensity,
        edges=edges,
        texture=texture,
        sigma_min=sigma_min,
        sigma_max=sigma_max,
    )
    num_features = test_features.shape[-1]

    # Prepare output Zarr array directly in the tomogram store
    print(f"Creating new feature store with {num_features} features...")
    copick_features = tomogram.new_features(feature_type)
    feature_store = copick_features.zarr()

    # Use the provided feature chunk size if available, otherwise default to the input chunk size
    if feature_chunk_size is None:
        feature_chunk_size = (num_features, *chunk_size)
    else:
        feature_chunk_size = (num_features, *feature_chunk_size)

    out_array = zarr.create(
        shape=(num_features, *image.shape),
        chunks=feature_chunk_size,
        dtype="float32",
        compressor=Blosc(cname="zstd", clevel=3, shuffle=2),
        store=feature_store,
        overwrite=True,
    )

    # Process each chunk
    for z in range(0, image.shape[0], chunk_size[0]):
        for y in range(0, image.shape[1], chunk_size[1]):
            for x in range(0, image.shape[2], chunk_size[2]):
                z_start = max(z - overlap, 0)
                z_end = min(z + chunk_size[0] + overlap, image.shape[0])
                y_start = max(y - overlap, 0)
                y_end = min(y + chunk_size[1] + overlap, image.shape[1])
                x_start = max(x - overlap, 0)
                x_end = min(x + chunk_size[2] + overlap, image.shape[2])

                chunk = image[z_start:z_end, y_start:y_end, x_start:x_end]
                chunk_features = multiscale_basic_features(
                    chunk,
                    intensity=intensity,
                    edges=edges,
                    texture=texture,
                    sigma_min=sigma_min,
                    sigma_max=sigma_max,
                )

                # Adjust indices for overlap
                z_slice = slice(overlap if z_start > 0 else 0, None if z_end == image.shape[0] else -overlap)
                y_slice = slice(overlap if y_start > 0 else 0, None if y_end == image.shape[1] else -overlap)
                x_slice = slice(overlap if x_start > 0 else 0, None if x_end == image.shape[2] else -overlap)

                # Ensure contiguous array and correct slicing
                contiguous_chunk = np.ascontiguousarray(chunk_features[z_slice, y_slice, x_slice].transpose(3, 0, 1, 2))

                out_array[
                    0:num_features,
                    z : z + chunk_size[0],
                    y : y + chunk_size[1],
                    x : x + chunk_size[2],
                ] = contiguous_chunk

    print(f"Features saved under feature type '{feature_type}'")
    return copick_features


if __name__ == "__main__":
    root = None  # copick.from_file
    tomo = None  # get a tomogram from root
    compute_skimage_features(
        tomogram=tomo,
        feature_type="skimageFeatures",
        copick_root=root,
        intensity=True,
        edges=True,
        texture=True,
        sigma_min=0.5,
        sigma_max=16.0,
        feature_chunk_size=None,  # Default to detected chunk size
    )
