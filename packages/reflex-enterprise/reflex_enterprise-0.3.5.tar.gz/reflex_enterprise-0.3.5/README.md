# How to install reflex_enterprise.   

```bash
pip install reflex-enterprise
```

# How to use reflex enterprise.   
In the main file, instead of using `rx.App()` to create your app, use the following:


## In the main file
```python
import reflex_enterprise as rxe

...

rxe.App()

...
```

## In rxconfig.py
```python
import reflex_enterprise as rxe

config = rxe.Config(
    app_name="MyApp",
    ... # you can pass all rx.Config arguments as well as the one specific to rxe.Config
)
```

### Enterprise features

| Feature | Description | Minimum Tier (Cloud) | Minimum Tier (Self-hosted) |
| --- | --- | --- | --- |
| `show_built_with_reflex` | Toggle the "Built with Reflex" badge. | Pro | Team|
| `use_single_port` | Enable one-port by proxying from backend to frontend. | - | Team |
