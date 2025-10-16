# JskToolBox

JskToolBox provides curated sets of Python classes that support system automation, networking,
configuration handling, and Tkinter-based GUI development. The documentation in `docs/` offers
module-by-module guides; the sections below highlight the available references.

## Core Utilities

- **AttribTool** – base classes that restrict dynamic attribute creation and manage declared fields  
  [AttribTool Readme](https://github.com/Szumak75/JskToolBox/blob/1.2.0/docs/AttribTool.md)
- **BaseTool** – mixins for metadata reporting, data storage, logging, and threading used across the project  
  [BaseTool Readme](https://github.com/Szumak75/JskToolBox/blob/1.2.0/docs/BaseTool.md)
- **RaiseTool** – helpers that standardise exception formatting and error reporting  
  [RaiseTool Readme](https://github.com/Szumak75/JskToolBox/blob/1.2.0/docs/RaiseTool.md)
- **SystemTool** – utilities for interacting with the host operating system  
  [SystemTool Readme](https://github.com/Szumak75/JskToolBox/blob/1.2.0/docs/SystemTool.md)

## Configuration and Data

- **ConfigTool** – parsers and helpers for working with configuration files  
  [ConfigTool Readme](https://github.com/Szumak75/JskToolBox/blob/1.2.0/docs/ConfigTool.md)
- **DateTool** – date/time conversions, validation, and formatting helpers  
  [DateTool Readme](https://github.com/Szumak75/JskToolBox/blob/1.2.0/docs/DateTool.md)
- **StringTool** – routines for text manipulation and sanitising  
  [StringTool Readme](https://github.com/Szumak75/JskToolBox/blob/1.2.0/docs/StringTool.md)

## Logging and Networking

- **LogsTool** – components that assemble the project logging subsystem (queues, formatters, workers)  
  [LogsTool Readme](https://github.com/Szumak75/JskToolBox/blob/1.2.0/docs/LogsTool.md)
- **NetTool** – general-purpose classes for networking tasks  
  [NetTool Readme](https://github.com/Szumak75/JskToolBox/blob/1.2.0/docs/NetTool.md)
- **NetAddressTool** – toolkits for IP addressing with dedicated IPv4 and IPv6 guides  
  [NetAddressTool Readme](https://github.com/Szumak75/JskToolBox/blob/1.2.0/docs/NetAddressTool.md)  
  [NetAddressTool IPv4 Readme](https://github.com/Szumak75/JskToolBox/blob/1.2.0/docs/NetAddressTool4.md)  
  [NetAddressTool IPv6 Readme](https://github.com/Szumak75/JskToolBox/blob/1.2.0/docs/NetAddressTool6.md)

## Tkinter

- **TkTool** – Tk mixins, layout helpers, clipboard adapters, and reusable widgets (excluding the unreliable `_TkClip`)  
  [TkTool Readme](https://github.com/Szumak75/JskToolBox/blob/1.2.0/docs/TkTool.md)

## Examples

Examples demonstrating selected modules can be found in  
[docs/examples](https://github.com/Szumak75/JskToolBox/tree/1.2.0/docs/examples).
