# Buyback Program

An Alliance Auth app for creating buyback programs and to allow users calculate prices for buyback contracts. Designed to be very transparent for the user and fast to use for the managers.

[![pipeline](https://gitlab.com/paulipa/allianceauth-buyback-program/badges/master/pipeline.svg)](https://gitlab.com/paulipa/allianceauth-buyback-program/-/commits/master)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/pre-commit/pre-commit)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![chat](https://img.shields.io/discord/790364535294132234)](https://discord.gg/zmh52wnfvM)

## Contents

- [Images](#images)
- [Features](#features)
- [Installation](#installation)
- [Program Settings](#program-settings)
- [Change Log](CHANGELOG.md)

## Images

![buyback_programs](/uploads/5ed1638501915e936d2e8177f4580da1/buyback_programs.png)
![item_details](/uploads/d124c70b15b36490c79b907fa25f768d/item_details.png)
![calculator](/uploads/47726510c6d6effa0e856e5ad5ca1688/calculator.png)
![program_statics](/uploads/e370ec69a3d050ecff4c4e7a19ec8849/program_statics.png)

## Features

- Multiple programs with their own settings
- Multiple owners
- Supports corporation and character owners
- Flexible program settings:
  - Allow all items
  - Allow only specific items
  - Custom location names
  - Global program tax
  - Item specified tax
  - Hauling fuel cost
  - Dynamic low price density tax
  - NPC price for NPC buy orders
- Best price variant for ore:
  - Supports raw, compressed, refined and any combination of the 3.
  - Will calculate price by the best available pricing method
- Allow / disallow unpacked items
- Restrict program to:
  - States
  - Groups
  - Open for everyone
- Personal buyback static tracking for:
  - Outstanding contracts
  - Finished contracts
- Program tracking for owners:
  - Outstanding contracts
  - Total bought value
- Contract abuse checker and notifications
  - Check if items do not match the calculated contract
  - Check if price does not match the calculated contract
  - Check if contract is made at wrong location
  - Check if contract is made incorrectly to corporation or character
  - Check extra characters in contract title
  - Check if contract contains donations
  - Check for scam contracts mimicing buyback contracts
- Contract tracking history
- Supports base price sources from:
  - [Fuzzwork API](https://market.fuzzwork.co.uk/api/)
  - [Janice API](https://janice.e-351.com/api/rest/docs/index.html)
  - Use buy, sell or split price as source
  - Use 5% top average or instant prices for source
- Supports discord notifications
  - Notifications for accepted contracts
  - Notifications for new contracts
  - For [aa-discordbot](https://github.com/pvyParts/allianceauth-discordbot)
  - For [discordproxy](https://gitlab.com/ErikKalkoken/discordproxy)

## Installation

### Step 1 - Prerequisites

1. Buyback program is a plugin for Alliance Auth. If you don't have Alliance Auth running already, please install it first before proceeding. (see the official [AA installation guide](https://allianceauth.readthedocs.io/en/latest/installation/auth/allianceauth/) for details)
1. Buyback program needs the app [django-eveuniverse](https://gitlab.com/ErikKalkoken/django-eveuniverse) to function. Please make sure it is installed, before before continuing.

### Step 2 - Install App

1. Activate your venv ```source /home/allianceserver/venv/auth/bin/activate```
1. Install the plugin ```pip install aa-buybackprogram```
1. Add ```'buybackprogram',``` into your settings/local.py installed apps section
1. Run migrations ```python manage.py migrate```
1. Collect static files ```python manage.py collectstatic```
1. Reload supervisor

### Step 3 - Update EVE Online API Application

Update the Eve Online API app used for authentication in your AA installation to include the following scopes:

- `esi-contracts.read_character_contracts.v1`
- `esi-contracts.read_corporation_contracts.v1`
- `esi-universe.read_structures.v1`

### Step 4 - Data Preload

Buybackprogram requires a lot of data to function as it is designed to allow your clients to sell you any items that exists in EVE. For this reason pre-loading all the date will take a while. Data pre-loading is used to decrease the amount of API calls made to type and price fetches.

#### Preload Load Type Data

To load type data run the command ```python manage.py buybackprogram_load_data```. This will start the preload of all `EveType`, `SolarSystem`, `EveMarketGroup` and `EveTypeMaterial` objects.

You can follow the progress of the load from your auth dashboard. This task can spike up easily over 100.000 tasks at a time so it is very normal that the queue grows very large while running this task.

> :warning: You will need to wait for the type data to load up before you can start to use the plugin. Trying to adjust program settings while the required data has not been yet loaded may result in failure of adjusting the settings.

#### Preload Price Data

After you have preloaded the type data you can preload price data into the database. Price data preloading is not mandatory but will speed up the first buyback calculations.

> :information_source: If price information is not found for items when the prices are calculated the first time the prices for that item will be fetched during the calculation process. This will increase the calculation time for the contract.

To preload price data run ```python manage.py buybackprogram_load_prices```

### Step 5 - Configure Auth settings

Buyback program requires a few periodic tasks to operate and update its data.

Buybackprogram is designed to use locally stored prices to speed up the price calculations. It is important that you have the price update task in your periodic tasks so that your prices will update.

By adding the following lines in your `local.py` setting file the program will update the stored item prices at midnight. This same task is also responsible for maintenance tasks such as removing unlinked tracking objects. It will also check for any new contracts and update the statistics page with them every 30 minutes:

```python
# Buybackprogram price updates, updates prices at midnight
CELERYBEAT_SCHEDULE['buybackprogram_update_all_prices'] = {
    'task': 'buybackprogram.tasks.update_all_prices',
    'schedule': crontab(minute=0, hour='0'),
}

# Buybackprogram contract updates, updates contracts every 30 minutes
CELERYBEAT_SCHEDULE['buybackprogram_update_all_contracts'] = {
    'task': 'buybackprogram.tasks.update_all_contracts',
    'schedule': crontab(minute='*/30'),
}

# Buybackprogram program performance updates, updates performance at midnight
CELERYBEAT_SCHEDULE['buybackprogram_update_program_performance'] = {
    'task': 'buybackprogram.tasks.update_program_performance',
    'schedule': crontab(minute=0, hour='0'),
}
```

#### Additional settings

You may change the following settings by adding the lines in your `local.py` setting files

Name | Description | Default | Options
-- | -- | -- | --
BUYBACKPROGRAM_TRACKING_PREFILL | This is the prefill tag you will have on the tracking description for your contracts | aa-bbp. | Free text input
BUYBACKPROGRAM_PRICE_SOURCE_ID | Station ID for fetching base prices. Supports IDs listed on [Fuzzwork API](https://market.fuzzwork.co.uk/api/). Does not work with Janice API!| 60003760 | See ID list
BUYBACKPROGRAM_PRICE_SOURCE_NAME | Display name of your price source. Has no effect on the actual price fetch which uses the ID. | Jita | Free text input
BUYBACKPROGRAM_PRICE_AGE_WARNING_LIMIT | Limit in hours when an item price is considered as outdated | 48
BUYBACKPROGRAM_PRICE_METHOD | By default Fuzzwork API will be used for pricing, if this is set to "Janice" then the Janice API will be used. | Fuzzwork | `Fuzzwork`, `Janice`
BUYBACKPROGRAM_PRICE_INSTANT_PRICES | On default we use top 5% average prices. Set to `true` to change to instant prices | False | `False`, `True`
BUYBACKPROGRAM_PRICE_JANICE_API_KEY | The API key to access Janice API. | `null` | `G9KwKq3465588VPd6747t95Zh94q3W2E`
BUYBACKPROGRAM_UNUSED_TRACKING_PURGE_LIMIT | Time limit to remove unlinked tracking objects from the database. Set to 0 to never purge any tracking objects. | 48 | Any number in hours
BUYBACKPROGRAM_TRACK_PREFILL_CONTRACTS | Determines if we will track and store contracts that starts with the prefill phrase but do not have any actual tracking hits in database | True | `True`, `False`

Note: If you change your price source for an old install you need to wait for the price update task to run or manually run it to update your current database prices.

Note: Using Janice API, Jita 4-4 prices will be used with the top 5% average price of the 5 day median price for buy and sell orders. No other price sources can be used with Janice

### Step 6 - Adjust Permissions

Overview of all permissions in this program. Note that all permissions are in the "general" section.

Name | Purpose | Example Target Audience
-- | -- | --
basic_access | Can access this app and see own statics. Can use buyback programs that are allowed by the buyback restriction rules. | Member State
manage_programs | Can create new locations and buyback programs and manage their own buyback programs. Can see own buyback programs statics. | Buyback managers
see_leaderboard | Can see the leaderboard stats for the programs that are visible for the user | Member State
see_performance | Can see the performance stats for the programs that are visible to the user | Member / Managers
see_all_statics | Can see all statistics in all buyback programs | Leadership

### Step 7 - Program Setup

After you have preloaded all the needed data you can start to setup programs.

Each user with `manage_programs` permission is able to setup their own buyback programs.

#### Managers

Each buyback program is operated by a manager. To add a new manager click on the `setup manager` button.

#### Locations

Each buyback program operates at a location that is constructed of `SolarSystem` and a `Custom name` and an optional `Structure ID`. To add a new location click on the `add location` button on the buyback page.

##### Solar System & Name

Find a solar system by typing in the solar system box. Then determine a name for the structure. Most often you want to use the actual in-game name of the structure so that people are able to identify the location.

The solar system name will indicate your sellers where the program contract structure is located. The name will describe the structure name in where the contracts should be created and most often should be identical to the actual structure name in-game.

##### Structure ID

Structure ID is optional and will enable contract location tracking in the program statistics page. If a program location has been given a structure ID the statistics page will display a warning if the user has made the actual contract from some other structure than the one that was determined in the buyback program.

The easiest way to find the actual structure id is to link the structure name into any chat box and post the structure name into the chat. This can be done in any channel or the structure name can be also copied from any MOTDs.

After you have posted the structure name in the chat right click it and press copy. You can now paste the structure into notepad or any other text editor and your output should look like this:

```plain
[17:37:54] Ikarus Cesaille > <url=showinfo:35826//1037962518481>Oisio - LinkNet Central Station</url> `
```

The unique structure ID for your structure is then `1037962518481`. Adding the ID to the location ID field will check if the contract creation location matches this ID.

### Step 8 - Create Program

Once you have created a location and added at least one manager you can setup the actual program. Click on the `create program` button to create a new program.

#### Program settings

Each program can be customized based on your needs. When setting up select the settings you wish to use.

##### Name/Description

A display name for your program

##### Manager

This is the character or the characters corporation which will be used as the assign to target for buyback contracts at this location. To add more owners use the `add manager` button. You can only see your own characters.

##### Is Corporation

If you wish that the contracts are assigned to the owners corporation instead of the character tick this box.

##### Location

The location where contracts should be created at. Only these locations are accepted

##### Expiration

Expiration time the contracts should bet set to.

##### Price type

You can select what price type is used as the base price for your calculations. You can select from either buy, sell or split prices.

##### Default tax

This is a general tax which is applied on all items in this program. If you wish to not allow all items in this program you can leave this to 0.

General tax is applied on all items sold via the buyback. You can add additional taxes on individual items or ban them from being accepted to the program once you have created the program.

##### Hauling fuel cost

You can add a fuel cost expense that is applied on each item sold via this program based on the volume of the item.

> :information_source: This setting is aimed more to null sec buyback programs to make it easier to calculate your taxes and display your members the expenses you have when selling.

##### Price density modifier

You can use a price density modifier which will add a additional tax on items with low price per volume ratio such as T1 ships.

> :information_source: This setting is aimer more at high sec buyback programs.

##### Ore volume based on compressed volume

Using this setting will calculate all items that can be compressed (mainly ore and ice) based on the compressed variant volume and use this volume instead of the raw volume to calculate the hauling and price dencity costs. This setting is mainly aimed at null sec where you might get raw ore sold to you but want to compress it before shipping as raw ore volume is very high and will cause high hauling costs.

##### Price density threshold

This is the lowest isk/m^3 ratio for items that are accepted to the program without the price density tax. Finding your own limits depends on your logistical department.

For example: Tritanium is 500 ISK/m³ @ 5 ISK per unit price. PLEX is 14,5Trillion ISK/m³ @2.9M per unit price.

##### Price density tax

This is the tax which will be applied to items with a price density below the price density threshold

> :warning: You should avoid using both the hauling fuel cost and the price density modifier at the same time as their function is fairly similar.

##### Allow all items

If you wish to allow any types of items to be sold via this program keep this box ticker.

You can determine individual increased taxes or ban items from being accepted to this program after creating the program.

If you do not want to accept all items you can set this box to False. By doing this you will need to set up a tax for each item you wish to accept into the program individually.

#### Ore settings

Ore type items such as asteroid, moon goo and ice have additional pricing methods you can use. You can use a mix of any of the three pricing models.

> :information_source: When using more than one pricing model the best price will be used as the buy value.

##### Use Refined value

If you wish to calculate ore buyback value based on the mineral values tick this box.

##### Use compressed value

If you want to use compressed value as a pricing method tick this box.

##### Use raw ore value

If you want to use raw ore value as a pricing method you can tick this box. Note that some ores such as Kernite and Moon Goo do not represent the real mineral value of the ores.

You can also individually ban raw ore types from the program. If you have an other option than the raw ore value selected the price will be calculated based on the other pricing models.

##### Allow unpacked items

Most often you want to buy only items that are packed. This will ensure that people do not sell items such as broken ammo crystals for you.

##### Refining rate

The refining rate is used in combination with the use refined value option.

#### Blue loot npc price

If you cant to use NPC buy order prices for blue loot (Sleeper loot) instead of Jita prices check this box. NPC price for these items will always be used even when Jita price would be higher.

#### Red loot npc price

If you cant to use NPC buy order prices for red loot (Triglavian loot) instead of Jita prices check this box. NPC price for these items will always be used even when Jita price would be higher.

#### Restrictions

You can restrict the visibility of the buyback programs to groups and states with the restriction options.

If no options are selected the program will be visible for everyone with the `basic_access` role.

> :no_entry: Do not mix group and state restrictions as this may lead into logic error. If you need to mix then create a separate programs for them.

#### Discord DM messages

If you want to receive messages over discord for every new contract you can tick this box.

> :information_source: Requires the [aa-discordbot plugin](https://github.com/pvyParts/allianceauth-discordbot) or [discordproxy app](https://gitlab.com/ErikKalkoken/discordproxy) to work

#### Show list of items on discord message

This option will determine if a list of all contract items is added into the discord message description field. If you are accepting all items the list may become very long. If set to false will show a link to the tracking page instead.

#### Discord channel messages

You can send notifications about new contracts directly into the discord channel which is linked to AUTH,

> :information_source: Requires the [aa-discordbot plugin](https://github.com/pvyParts/allianceauth-discordbot) or [discordproxy app](https://gitlab.com/ErikKalkoken/discordproxy) to work

### Step 9 - Special Taxes

You can modify individual item settings or allow items for a program that has set `allow all items = False` via the `special taxes` menu for each program.

Set a item specific tax for each item. The tax wil be applied on top of the default tax for the program. You can also disallow an item from being accepted in the contract completely.

> :information_source: The item specific tax can also be a negative value allowing you to decrease taxes on certain items.

To adjust individual item taxes inside a program click on the `Special taxes` button next to your program.

You can either add items one by one with the `add item` button or add all items that belongs to a market group and every sub-child market group of that group with `add market group`

You can edit an item on the taxation table simply by adding it again. To delete the item press the delete button next to it or to delete all items in the program click on the delete all items button.

#### Market Groups

When you add an market group each item inside that market group, the child of the market group and the child of the child group will be added to the item taxes (3 steps down)

The easiest way to check which items are under which market group is to open the market window in-game or third party programs such as [https://evemarketer.com/](https://evemarketer.com/)

Example:

Market group `Minerals` is the bottom market group that includes the standard minerals. Adding this market group to the taxation will add 8 items to the taxes (Tritanium, Pyerite etc.)

Market group `Standard ores` is a parent category and there are no direct items under this category. However this category has child categories such as Veldspar, Jaspet, Scordite which each includes multiple variations of the ores. Adding the `Standard ores` category will add each ore type to the special tax section.

#### Most Common Groups

Name | Includes | Items
-- | --
Standard Ores | Normal ores from belts and anomalies | Veldspar, Hedbergite, Compressed Arkonor ...
Moon Ores | Ores from moon mining | Cobaltite, Loparite, Pollucite
Ice Ores | Ores from ice mining | Blue Ice, Dark Glitter, Compressed Blue Ice ....
Minerals | Contains materials for refining Standard Ore | Tritanium, Pyerite ....
Salvage Materials | Salvage from loot | Armor Plates, Trigger Unit, Ancient Radar Decorrelator ...
