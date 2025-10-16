# Taiwan CWA Weather MCP Server

Access Taiwan Central Weather Administration (CWA) weather data and forecasts through the Model Context Protocol.

<!-- mcp-name: io.github.nigue3025/tw-cwa-weather-mcp -->

## Features

- Get weather forecasts for all Taiwan counties and cities
- List available locations
- Support for location aliases
- Real-time data from Taiwan CWA OpenData API

## Tools

### get_weather
Get weather forecast data for a specific Taiwan location.

**Parameters:**
- `given_location` (string): The county or city name (supports both Chinese and aliases)

**Returns:** Weather forecast data including temperature, rainfall probability, weather conditions, and comfort level.

### list_available_locations
List all available Taiwan counties/cities and their aliases.

**Returns:** Complete list of supported locations and their alternative names.

## Installation

```bash
pip install tw-cwa-weather-mcp
```

## Configuration

You need a Taiwan CWA API key to use this server. Create a file named `GOV_api_key.txt` in the server directory with your API key.

Get your API key from: https://opendata.cwa.gov.tw/

## Usage

Add to your MCP client configuration:

```json
{
  "mcpServers": {
    "taiwan-weather": {
      "command": "python",
      "args": ["-m", "tw_cwa_weather_mcp"]
    }
  }
}
```

## Development

This server uses FastMCP to provide Taiwan weather data through the Model Context Protocol.

## License

MIT License

## Author

nigue3025
