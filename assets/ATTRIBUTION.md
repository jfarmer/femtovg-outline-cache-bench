# Runtime asset attribution

Font files are unmodified copies of the exact benchmark inputs. The source
manifest records their SHA-256 checksums. These licenses also cover matching
copies inside the pinned source snapshots.

| File | Copyright / source | License text |
| --- | --- | --- |
| RobotoFlex-VariableFont.ttf | Copyright 2017 The Roboto Flex Project Authors; [Roboto Flex](https://github.com/TypeNetwork/Roboto-Flex) | [OFL 1.1](licenses/RobotoFlex-OFL.txt) |
| Vollkorn-Medium.ttf | Copyright 2017 The Vollkorn Project Authors | [OFL 1.1](licenses/Vollkorn-OFL.txt) |
| PTSans-Regular.ttf | ParaType; exact PT Sans candidate used in the font study | [OFL 1.1](licenses/PTSans-OFL.txt) |
| LiberationSerif-Regular.ttf | Liberation Fonts, version 2.1.5 | [License](licenses/Liberation-LICENSE.txt) |
| amiri-regular.ttf | Copyright 2010, 2012 Khaled Hosny; portions copyright 2010 Sebastian Kosch; reserved name Amiri | [OFL 1.1 from the font name table](licenses/Amiri-OFL.txt) |
| BungeeColor-Subset.ttf | Copyright 2008 The Bungee Project Authors; upstream FemtoVG test fixture | [OFL 1.1](licenses/BungeeColor-OFL.txt) |
| entypo.ttf | Daniel Bruce, 2012; exact same SHA-256 as [NanoVG's example font](https://github.com/memononen/nanovg/blob/master/example/entypo.ttf) | [CC BY-SA 4.0](licenses/Entypo-CC-BY-SA-4.0.txt), as [documented by NanoVG](https://github.com/memononen/nanovg#license) |

The demo JPEGs (`images/image1.jpg` through `image12.jpg`, plus `pattern.jpg`)
are the unmodified example fixtures shipped in the pinned FemtoVG source,
which retains its MIT/Apache license notices. Their upstream paths and hashes
remain in the bundled source manifest. No new artwork was generated.

Arial is not distributed here. Historical Arial results retain the font-file
hash and metadata; a fresh Arial run requires a locally licensed installation
or an explicit user-supplied font path.
