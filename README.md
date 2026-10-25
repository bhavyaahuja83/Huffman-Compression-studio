# Huffman Compression Studio

HuffLab is a local desktop workbench for inspecting Huffman coding. Type or open
UTF-8 text to view its byte frequencies, Huffman tree, prefix codes and payload
statistics. Save the text to a `.huf` file and open it later to restore it.

## Run

```powershell
python -m pip install -r requirements.txt
python main.py
```

The core codec and `.huf` format use only the Python standard library.
`customtkinter` provides the desktop UI and `matplotlib` the frequency chart.

## File format and behavior

Text is encoded as UTF-8, then Huffman-coded one byte at a time. A `.huf` file
contains the `HUF1` signature, original byte count, meaningful bit count, a
sparse byte-frequency table and the packed payload. Unused bits in the final
payload byte are padding and are ignored during decoding.

An empty input has an empty tree and payload. A single distinct byte uses the
code `0`, with one meaningful bit for each original byte. The UI reports actual
payload bits and actual `.huf` file size: headers and padding can make a file
larger than the original. The savings card compares payload bits to the
original's 8-bit-per-byte representation.

## Tests

```powershell
python -m pytest
```
