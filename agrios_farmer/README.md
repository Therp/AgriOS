# Agrios Farmer

# TODO RP: rename agrios_farmer into agrios_farmer.

This will become the base for all other agrios modules.

In this we will define:

- Farmers as a specific type of partner;
- Farmer groups;
- Location.

Location will be part of a configurable hierarchy, that will be defined per
country. The highest level will always be the country, below this can be regions
(or provinces), below that districts, below that communities, etc.

Each Farmer and each Farmer group will be located in a specific location.

# Separate Menu

The Agrios menu and Agrios Farmer app will be the single app to do everything Farmer related. For this
reason there will be a menu separate from the Contacts app, and partners that are
farmers will also not be shown in the Contacts app.

# Module structure To be realised

- agrios_farmer: base module, will contain farmers, farmer groups and location data;
- agrios_plot: will contain farmers plots and the products grown on
  those;
  - Will depend on agrios_farmer.
- agrios_account: will contain contracts, purchases (offtake) and sales (inputs);
  - Will depend on agrios_plot.
- agrios_training: will contain training, teachers, certification;
  - Will depend on agrios_farmer.
- agrios\hr: will contain hr information.
  - Will depend on agrios_farmer.
