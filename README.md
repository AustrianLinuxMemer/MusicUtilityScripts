# MusicUtilityScripts
A collection of Python scripts I maintain for a larger project of mine

# CLI interface
The CLI interface of these tools is quite easy to understand:

`tool_name IN_FILE OUT_FILE [META_JSON] [COVERS_JSON]`

- `IN_FILE`: The input media file, can be anything, these tools are supposed to swallow anything
- `OUT_FILE`: The output media file, This is usually in a format that tool_name is written for
- `META_JSON`: A JSON file whose schema is described in more detail in its own section. It is used to pass Vorbis-style tags to the tool
- `COVERS_JSON`: Same as `META_JSON`. It is used to pass ID3 APIC-coded Image files to the tool

# TAGS_JSON

A `TAGS`, also referenced as a `tags.json` is structured like this:

- `version`: A version string for the `policy` object
- `tags`: A dictionary of tags (case-insensitive keys) that contain each a list of tags
- `policy`: A policy object.


## Policy object

The policy object is used to pass additional info to the tool about how to format the tags. Version `1.0` supports these fields:

- `concat` (optional): Is an array with following values:
  - `[0]`: Boolean to indicate if tags should be concatenated
  - `[1]`: The string to be used if tags should be concatenated


# COVERS_JSON

A `COVERS_JSON`, also referenced as a `covers.json` is structured like this:

- `version`: A version string for the `policy` object
- `covers`: A dictionary of cover files
  - key: String representation of the ID3 APIC image type
  - value: A Cover Object
- `policy`: A policy object


## Policy object

The policy object is used to pass additional info to the tool about how to format the image files. Version `1.0` supports these fields:

- `mandatory` (Optional): Is an array containing ALL ID3 APIC image keys that HAVE to be included into the output file
- `format` (Optional): Is a MIME string directing which image file format to use for embedding covers. Each tool is supposed to provide a default image format but should also respect this override

## Cover object:

A Cover Object is an object that includes following required fields:

- `path`: An absolute path to the cover image file
- `size`: An array of integers of either size 1 or size 2, all other sizes are rejected
  - `[0]`: Width of the image, Required, Cannot be null
  - `[1]` (optional): Height of the image, if omitted or null, Width is used