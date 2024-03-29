from typing import Any
import arcade
import pytest
from pyglet.math import Vec2
from pytest import approx
from trainfinity2.constants import (
    GRID_WIDTH_CELLS,
    SECONDS_BETWEEN_CARGO_CREATION,
)
from trainfinity2.game import Mode, Game
from trainfinity2.model import (
    IronMine,
    Rail,
    CargoType,
    SignalColor,
    Station,
    SteelWorks,
    Water,
)
from tests.util import create_objects

check_call_count = 0


def check(statement: Any, count=[0]):
    """Pretty hacky way to ensure that we don't get any infinite loops.
    Does not reset the count between function calls, except if one hangs."""
    count[0] += 1
    if count[0] < 10000:
        return statement
    count[0] = 0  # pragma: no cov
    raise AssertionError("Max iterations reached")  # pragma: no cov


def test_draw(game: Game):
    create_objects(
        game.grid,
        """
        . M . F .

        .-S-.-S-.
        """,
    )
    game._create_train(*game.grid.station_from_position.values())
    # Mainly for code coverage
    game.trains[0].wagons[0].cargo_count[CargoType.IRON] == 1
    game.on_draw()


class TestClicks:
    def test_create_click(self, game: Game, monkeypatch):
        self.on_left_click_call_count = 0

        def mock_on_left_click(x, y):
            self.on_left_click_call_count += 1

        monkeypatch.setattr(game, "on_left_click", mock_on_left_click)

        game.on_mouse_press(0, 0, arcade.MOUSE_BUTTON_LEFT, modifiers=0)
        game.on_mouse_release(0, 0, arcade.MOUSE_BUTTON_LEFT, modifiers=0)

        assert self.on_left_click_call_count == 1


class TestCamera:
    def test_camera_starts_at_origo(self, game):
        assert game.camera.position == Vec2(0, 0)

    def test_camera_pans_when_right_clicking_and_dragging(self, game):
        game.on_mouse_press(x=100, y=100, button=arcade.MOUSE_BUTTON_RIGHT, modifiers=0)
        game.on_mouse_motion(x=200, y=300, dx=100, dy=200)
        game.on_mouse_release(
            x=200, y=300, button=arcade.MOUSE_BUTTON_RIGHT, modifiers=0
        )

        assert game.camera.position == Vec2(-100, -200)

    def test_camera_stops_panning_when_releasesing_mouse_button(self, game: Game):
        game.on_mouse_press(x=100, y=100, button=arcade.MOUSE_BUTTON_RIGHT, modifiers=0)
        game.on_mouse_motion(x=200, y=300, dx=100, dy=200)
        game.on_mouse_release(
            x=200, y=300, button=arcade.MOUSE_BUTTON_RIGHT, modifiers=0
        )
        game.on_mouse_motion(x=300, y=500, dx=100, dy=200)

        assert game.camera.position == Vec2(-100, -200)

    def test_camera_stops_when_trying_to_move_past_top_left_corner(self, game):
        game.on_mouse_press(x=100, y=100, button=arcade.MOUSE_BUTTON_RIGHT, modifiers=0)
        game.on_mouse_motion(x=2000, y=3000, dx=1900, dy=2900)
        game.on_mouse_release(
            x=2000, y=3000, button=arcade.MOUSE_BUTTON_RIGHT, modifiers=0
        )

        assert game.camera.position == Vec2(-400, -300)

    def test_camera_stops_when_trying_to_move_past_bottom_right_corner(self, game):
        game.on_mouse_press(x=100, y=100, button=arcade.MOUSE_BUTTON_RIGHT, modifiers=0)
        game.on_mouse_motion(x=-2000, y=-3000, dx=-2100, dy=-3100)
        game.on_mouse_release(
            x=-2000, y=-3000, button=arcade.MOUSE_BUTTON_RIGHT, modifiers=0
        )

        assert game.camera.position == Vec2(200, 300)

    def test_camera_starts_with_scale_1(self, game):
        assert game.camera.scale == 1.0

    def test_scrolling_up_zooms_in(self, game):
        game.on_mouse_scroll(x=100, y=100, scroll_x=0, scroll_y=1)

        assert game.camera.scale == approx(0.9)

    def test_scrolling_down_zooms_out(self, game):
        assert game.camera.scale == 1.0
        game.on_mouse_scroll(x=100, y=100, scroll_x=0, scroll_y=-1)

        assert game.camera.scale == approx(1.1)


class TestBuildingRail:
    def test_horizontal_rail_being_built(self, game: Game):
        game.on_mouse_press(x=90, y=90, button=arcade.MOUSE_BUTTON_LEFT, modifiers=0)
        game.on_mouse_motion(x=120, y=90, dx=30, dy=0)

        assert game.grid.rails_being_built == {Rail(3, 3, 4, 3)}

    def test_vertical_rail_being_built(self, game: Game):
        game.on_mouse_press(x=90, y=90, button=arcade.MOUSE_BUTTON_LEFT, modifiers=0)
        game.on_mouse_motion(x=90, y=120, dx=0, dy=30)

        assert game.grid.rails_being_built == {Rail(3, 3, 3, 4)}

    def test_diagonal_rail_being_built(self, game: Game):
        game.on_mouse_press(x=90, y=90, button=arcade.MOUSE_BUTTON_LEFT, modifiers=0)
        game.on_mouse_motion(x=120, y=120, dx=30, dy=30)

        assert game.grid.rails_being_built == {Rail(3, 3, 4, 4)}

    def test_non_straight_rail_being_built(self, game: Game):
        game.on_mouse_press(x=90, y=90, button=arcade.MOUSE_BUTTON_LEFT, modifiers=0)
        game.on_mouse_motion(x=120, y=150, dx=30, dy=60)

        assert game.grid.rails_being_built == {
            Rail(x1=3, y1=3, x2=3, y2=4),
            Rail(x1=3, y1=4, x2=4, y2=5),
        }

    def test_built_rail(self, game: Game):
        game.on_mouse_press(x=100, y=100, button=arcade.MOUSE_BUTTON_LEFT, modifiers=0)
        game.on_mouse_motion(x=130, y=100, dx=30, dy=0)
        game.on_mouse_release(
            x=130, y=100, button=arcade.MOUSE_BUTTON_LEFT, modifiers=0
        )

        assert len(game.grid.rails_being_built) == 0
        assert len(game.grid.rails) == 1

    def test_building_rail_twice_only_creates_one_set_of_rail_shapes(self, game: Game):
        for _ in range(2):
            game.on_mouse_press(
                x=100, y=100, button=arcade.MOUSE_BUTTON_LEFT, modifiers=0
            )
            game.on_mouse_motion(x=130, y=100, dx=30, dy=0)
            game.on_mouse_release(
                x=130, y=100, button=arcade.MOUSE_BUTTON_LEFT, modifiers=0
            )

        assert len(game.drawer._rail_shapes_from_object_id) == 1

    def test_cannot_build_rail_in_illegal_position(self, game: Game):
        game.grid.water = {Vec2(3, 3): Water(Vec2(3, 3))}

        game.on_mouse_press(x=100, y=100, button=arcade.MOUSE_BUTTON_LEFT, modifiers=0)
        game.on_mouse_motion(x=130, y=100, dx=30, dy=0)
        game.on_mouse_release(
            x=130, y=100, button=arcade.MOUSE_BUTTON_LEFT, modifiers=0
        )

        assert len(game.grid.rails) == 0

    def drag_one_tile_outside_grid(self, game: Game):
        game.on_mouse_press(x=15, y=15, button=arcade.MOUSE_BUTTON_LEFT, modifiers=0)
        game.on_mouse_motion(x=-15, y=15, dx=-30, dy=0)
        game.on_mouse_release(x=-15, y=15, button=arcade.MOUSE_BUTTON_LEFT, modifiers=0)

    def test_cannot_build_rail_outside_grid(self, game: Game):
        self.drag_one_tile_outside_grid(game)

        assert len(game.grid.rails) == 0

    def test_can_build_rail_outside_grid_when_grid_has_enlarged(self, game: Game):
        game.grid.level_up(2)
        game.gui.disable()
        self.drag_one_tile_outside_grid(game)

        assert len(game.grid.rails) == 1


class TestBuildingStations:
    def test_building_horizontal_station(self, game: Game):
        """
        D: where the drag occurs
        M: the mine
        .....
        .DDD.
        .M...
        """
        game.gui.disable()
        game.grid.create_building(IronMine(Vec2(1, 0)))
        game.gui.mode = Mode.STATION
        game.on_mouse_press(x=45, y=45, button=arcade.MOUSE_BUTTON_LEFT, modifiers=0)
        game.on_mouse_motion(x=105, y=45, dx=60, dy=0)
        game.on_mouse_release(x=105, y=45, button=arcade.MOUSE_BUTTON_LEFT, modifiers=0)

        positions = (Vec2(1, 1), Vec2(2, 1), Vec2(3, 1))

        assert game.grid.station_from_position[Vec2(1, 1)] == Station(
            positions=positions, east_west=True
        )

    def test_building_vertical_station(self, game: Game):
        """
        D: where the drag occurs
        F: the factory
        ...
        .D.
        .D.
        FD.
        ...
        """
        game.gui.disable()
        game.gui.mode = Mode.STATION
        game.grid.create_building(SteelWorks(Vec2(0, 1)))
        game.on_mouse_press(x=45, y=45, button=arcade.MOUSE_BUTTON_LEFT, modifiers=0)
        game.on_mouse_motion(x=45, y=105, dx=0, dy=60)
        game.on_mouse_release(x=45, y=105, button=arcade.MOUSE_BUTTON_LEFT, modifiers=0)

        positions = (Vec2(1, 1), Vec2(1, 2), Vec2(1, 3))

        assert game.grid.station_from_position[Vec2(1, 1)] == Station(
            positions=positions, east_west=False
        )

    def test_extending_station_removes_old_station(self, game: Game):
        create_objects(
            game.grid,
            """
            .-.-M-.-.

            .-.-S-S-.
            """,
        )
        game.gui.disable()
        game.gui.mode = Mode.STATION

        assert len(game.grid.stations) == 1
        assert len(list(game.grid.stations)[0].positions) == 2
        game.on_mouse_press(x=45, y=15, button=arcade.MOUSE_BUTTON_LEFT, modifiers=0)
        game.on_mouse_motion(x=75, y=15, dx=30, dy=0)
        game.on_mouse_release(x=75, y=15, button=arcade.MOUSE_BUTTON_LEFT, modifiers=0)

        assert len(game.grid.stations) == 1
        assert len(list(game.grid.stations)[0].positions) == 3


class TestGui:
    def test_game_starts_in_rail_mode(self, game: Game):
        assert game.gui.mode == Mode.RAIL

    def test_clicking_bottom_left_corner_switches_to_select_mode(self, game: Game):
        """Even works as long as press and release are both inside the box"""
        game.on_mouse_press(5, 5, arcade.MOUSE_BUTTON_LEFT, modifiers=0)
        game.on_mouse_release(25, 25, arcade.MOUSE_BUTTON_LEFT, modifiers=0)
        assert game.gui.mode == Mode.SELECT

    def test_mouse_down_on_bottom_left_corner_highlights_select_mode_button(
        self, game: Game
    ):
        game.on_mouse_press(15, 15, arcade.MOUSE_BUTTON_LEFT, modifiers=0)
        assert game.gui.mouse_press_box
        assert game.gui.mouse_press_box.mode == Mode.SELECT


class TestCreateTrain:
    # def test_clicking_nothing_in_train_mode_does_nothing(
    #     self, game_with_factory_and_mine: Game
    # ):
    #     """Mainly for code coverage"""
    #     # game = game_with_factory_and_mine
    #     # game.gui.mode = Mode.TRAIN
    #     # game.gui.disable()

    #     # game.on_left_click(100, 100)

    def test_clicking_station_in_train_mode_starts_a_train_placement_session(
        self, game: Game
    ):
        create_objects(
            game.grid,
            """
            . M . F .

            .-S-.-S-.
            """,
        )
        game.gui.mode = Mode.TRAIN
        game.gui.disable()

        assert not game._train_placer.session

        game.on_left_click(30, 0)

        assert game._train_placer.session

    def test_clicking_station_in_train_mode_highlights_station(self, game: Game):
        create_objects(
            game.grid,
            """
            . M . F .

            .-S-.-S-.
            """,
        )
        game.gui.mode = Mode.TRAIN
        game.gui.disable()

        assert len(game.drawer.highlight_shape_element_list) == 0

        # Click first station
        game.on_left_click(30, 0)

        assert len(game.drawer.highlight_shape_element_list) == 1

    def test_clicking_gui_stops_train_placing_session_and_removes_station_highlight(
        self, game: Game
    ):
        create_objects(
            game.grid,
            """
            . M . F .

            .-S-.-S-.
            """,
        )
        game.gui.mode = Mode.TRAIN
        game.gui.disable()
        game.on_left_click(30, 0)
        game.gui.enable()

        # Click GUI
        game.on_mouse_press(15, 15, arcade.MOUSE_BUTTON_LEFT, modifiers=0)
        game.on_mouse_release(15, 15, arcade.MOUSE_BUTTON_LEFT, modifiers=0)

        assert not game._train_placer.session
        assert len(game.drawer.highlight_shape_element_list) == 0

    @pytest.fixture
    def hover_over_connected_station(self, game: Game):
        create_objects(
            game.grid,
            """
            . M . F .

            .-S-.-S-.
            """,
        )
        game.gui.mode = Mode.TRAIN
        game.gui.disable()

        # Click first station
        game.on_left_click(30, 0)
        # Hover over next station
        game.on_mouse_motion(90, 0, 0, 0)
        return game

    def test_hovering_over_connected_station_highlights_route(
        self, hover_over_connected_station: Game
    ):
        game = hover_over_connected_station
        assert len(game.drawer.highlight_shape_element_list) == 3

    def test_stopping_hovering_over_connected_station_only_highlights_station_again(
        self, hover_over_connected_station: Game
    ):
        game = hover_over_connected_station
        # Hover outside station
        game.on_mouse_motion(500, 500, 0, 0)

        assert len(game.drawer.highlight_shape_element_list) == 1

    def test_clicking_two_connected_stations_creates_train(self, game: Game):
        create_objects(
            game.grid,
            """
            . M . F .

            .-S-.-S-.
            """,
        )
        game.gui.mode = Mode.TRAIN

        # Click first station
        game.on_left_click(30, 0)
        # Click next station
        game.on_left_click(90, 0)

        assert len(game.trains) == 1

    def test_clicking_two_connected_stations_creates_train_that_starts_moving(
        self, game: Game
    ):
        create_objects(
            game.grid,
            """
            . M . F .

            .-S-.-S-.
            """,
        )
        game.gui.mode = Mode.TRAIN

        # Click first station
        game.on_left_click(30, 0)
        # Click next station
        game.on_left_click(90, 0)

        while check(game.trains[0].x < 1.5):
            game.on_update(1 / 60)

    def test_clicking_two_connected_stations_of_size_2_creates_train_that_starts_moving(
        self, game: Game
    ):
        create_objects(
            game.grid,
            """
            . M . . F . .

            .-S-S-.-S-S-.
            """,
        )
        game.gui.mode = Mode.TRAIN

        # Click first station
        game.on_left_click(30, 0)
        # Click next station
        game.on_left_click(120, 0)

        while check(game.trains[0].x < 3.0):
            game.on_update(1 / 60)

    def test_clicking_two_connected_stations_removes_highlight(self, game: Game):
        create_objects(
            game.grid,
            """
            . M . F .

            .-S-.-S-.
            """,
        )
        game.gui.mode = Mode.TRAIN

        # Click first station
        game.on_left_click(30, 0)
        # Click next station
        game.on_left_click(90, 0)

        assert len(game.drawer.highlight_shape_element_list) == 0

    def test_clicking_two_unconnected_stations_does_not_create_train(self, game: Game):
        create_objects(
            game.grid,
            """
            . M . F .

            .-S .-S-.
            """,
        )
        game.gui.mode = Mode.TRAIN

        # Click first station
        game.on_left_click(30, 0)
        # Click next station
        game.on_left_click(30, 90)

        assert len(game.trains) == 0

    def test_clicking_the_same_station_twice_removes_highlight_and_does_not_create_train(
        self, game: Game
    ):
        create_objects(
            game.grid,
            """
            . M . F .

            .-S-.-S-.
            """,
        )
        game.gui.mode = Mode.TRAIN

        game.on_left_click(30, 0)
        game.on_left_click(30, 0)

        assert len(game.trains) == 0
        assert len(game.drawer.highlight_shape_element_list) == 0

    @pytest.fixture
    def two_trains(self, game):
        create_objects(
            game.grid,
            """
            . M . F .

            .-S-.-S-.
            """,
        )
        game.gui.mode = Mode.TRAIN

        # Click first station
        game.on_left_click(30, 0)
        # Click next station
        game.on_left_click(90, 0)

        game.gui.mode = Mode.TRAIN
        # Click first station
        game.on_left_click(30, 0)
        # Click next station
        game.on_left_click(90, 0)

        return game

    def test_create_two_trains(self, two_trains: Game):
        assert len(two_trains.trains) == 2

    def test_two_trains_colliding_are_destroyed(self, two_trains: Game):
        two_trains.on_update(1 / 60)
        assert len(two_trains.trains) == 0

    # def test_destroying_the_rails_under_train_destroys_train(self, game: Game):
    #     create_objects(
    #         game.grid,
    #         """
    #         . M . F .

    #         .-S-.-S-.
    #         """,
    #     )
    #     game._create_train(*game.grid.stations.values())
    #     train = game.trains[0]
    #     train.target_x = 30
    #     game.grid.remove_rail(Vec2(30, 0))
    #     game.on_update(1 / 60)
    #     assert not game.trains

    def test_destroying_rail_on_train_route_does_not_crash_game(self, game: Game):
        create_objects(
            game.grid,
            """
            . M . F .

            .-S-.-S-.
            """,
        )
        game._create_train(*game.grid.station_from_position.values())
        train = game.trains[0]
        train.target_x = 1
        game.grid.remove_rail(Vec2(60, 0))
        game.on_update(1 / 60)

    def test_cannot_create_train_in_reserved_signal_block(self, game: Game):
        create_objects(
            game.grid,
            """
            . M . F .

            .-S-.-S-.
            """,
        )
        game.gui.mode = Mode.TRAIN

        # Click first station
        game.on_left_click(30, 0)
        # Click next station
        game.on_left_click(90, 0)

        assert not game.signal_controller.reserver(Vec2(1, 0))
        while check(game.trains[0].speed == 0.0):
            game.on_update(1 / 60)
        assert game.signal_controller.reserver(Vec2(1, 0))

        game.gui.mode = Mode.TRAIN
        # Click first station
        game.on_left_click(30, 0)
        # Click next station
        game.on_left_click(90, 0)

        assert game.gui.mode == Mode.TRAIN
        assert len(game.trains) == 1


class TestDestroyMode:
    def test_hovering_in_destroy_mode_highlights_rails_to_be_destroyed(
        self,
        game: Game,
    ):
        create_objects(
            game.grid,
            """
            .-.
            """,
        )
        game.gui.mode = Mode.DESTROY
        game.gui.disable()

        assert len(game.drawer.rail_to_be_destroyed_shape_list) == 0

        game.on_mouse_motion(x=15, y=15, dx=0, dy=0)

        # 12 is the number of shapes a rail consists of when writing this test
        assert len(game.drawer.rail_to_be_destroyed_shape_list) == 12

    def test_clicking_in_destroy_mode_destroys_station_and_rail(
        self,
        game: Game,
    ):
        create_objects(
            game.grid,
            """
            . M . F .

            .-S-.-S-.
            """,
        )
        game.gui.mode = Mode.DESTROY
        game.gui.disable()

        assert len(game.grid.station_from_position) == 2
        assert len(game.grid.rails) == 4

        game.on_left_click(x=45, y=15)

        assert len(game.grid.station_from_position) == 1
        assert len(game.grid.rails) == 2

    def test_clicking_in_destroy_mode_destroys_rail(self, game: Game):
        create_objects(
            game.grid,
            """
            .-.-.
            """,
        )
        game.gui.mode = Mode.DESTROY
        game.gui.disable()

        assert len(game.grid.rails) == 2

        game.on_left_click(15, 15)

        assert len(game.grid.rails) == 1


def test_iron_is_regularly_added_to_mines(game: Game):
    create_objects(
        game.grid,
        """
        . M . F .

        .-S-.-S-.
        """,
    )
    # Start just before creating a new iron
    game.cargo_counter = SECONDS_BETWEEN_CARGO_CREATION - 0.00001

    game.on_update(1 / 60)

    assert game.grid.buildings[Vec2(1, 1)].cargo_count[CargoType.IRON] == 1
    assert (
        len(game.drawer.cargo_shape_element_list) == 2
    )  # One for the interior, one for the frame


class TestTrainMoving:
    def test_trains_are_moved_in_on_update(self, game: Game):
        create_objects(
            game.grid,
            """
            . M . F .

            .-S-.-S-.
            """,
        )
        game._create_train(*game.grid.station_from_position.values())
        # For code coverage
        game.on_update(1 / 60)

    def test_train_speed_is_set_to_0_when_passing_corner(self, game: Game):
        """The train starts at 1,0 and the corner is at 60,0"""
        create_objects(
            game.grid,
            """
            . M s F
                |
            .-S-. .
            """,
        )
        train = game._create_train(*game.grid.station_from_position.values())
        # For code coverage
        while check(train.speed == 0.0):
            game.on_update(1 / 60)
        while check(train.speed > 0):
            game.on_update(1 / 60)
        assert 1.9 < train.x < 2.1


def test_fps_is_updated_every_second(game: Game):
    # For code coverage
    game.seconds_since_last_gui_figures_update = 0.99

    game.on_update(1 / 60)


def test_train_picks_up_iron_from_mine(game: Game):
    create_objects(
        game.grid,
        """
        . M . F .

        .-S-.-S-.
        """,
    )
    game._create_train(*game.grid.station_from_position.values())
    mine = game.grid.buildings[Vec2(1, 1)]
    train = game.trains[0]
    game.try_create_cargo_in_all_buildings()
    train.x = 1
    train.target_x = 1
    train._target_station = game.grid.station_from_position[Vec2(1, 0)]
    assert mine.cargo_count[CargoType.IRON] == 1
    assert train.wagons[0].cargo_count[CargoType.IRON] == 0
    assert len(game.drawer.cargo_shape_element_list) == 2

    while check(train.wagons[0].cargo_count[CargoType.IRON] == 0):
        game.on_update(1 / 60)

    assert mine.cargo_count[CargoType.IRON] == 0
    assert train.wagons[0].cargo_count[CargoType.IRON] == 1
    assert len(game.drawer.cargo_shape_element_list) == 0


def test_train_delivers_iron_to_market_gives_money(game: Game):
    create_objects(
        game.grid,
        """
        . M . m .

        .-S-.-S-.
        """,
    )
    game._create_train(*game.grid.station_from_position.values())
    train = game.trains[0]
    train.wagons[0].cargo_count[CargoType.IRON] = 1
    train.x = 3
    train.target_x = 3
    train._target_station = game.grid.station_from_position[Vec2(3, 0)]

    while check(train.wagons[0].cargo_count[CargoType.IRON]):
        game.on_update(1 / 60)

    assert train.wagons[0].cargo_count[CargoType.IRON] == 0
    assert game.player.money == 1


def test_on_resize(game):
    # For code coverage
    game.on_resize(800, 600)


class TestSelect:
    def test_clicking_outside_all_trains_in_select_mode_deselects_all_trains(
        self, game: Game
    ):
        create_objects(
            game.grid,
            """
            . M . F .

            .-S-.-S-.
            """,
        )
        game._create_train(*game.grid.station_from_position.values())
        game.gui.disable()
        game.gui.mode = Mode.SELECT
        train = game.trains[0]
        train.selected = True

        game.on_left_click(500, 500)

        assert not train.selected

    def test_clicking_gui_deselects_all_trains(self, game: Game):
        create_objects(
            game.grid,
            """
            . M . F .

            .-S-.-S-.
            """,
        )
        game._create_train(*game.grid.station_from_position.values())
        train = game.trains[0]
        train.selected = True

        game.on_mouse_press(15, 15, arcade.MOUSE_BUTTON_LEFT, 0)
        game.on_mouse_release(15, 15, arcade.MOUSE_BUTTON_LEFT, 0)

        assert not train.selected

    def test_clicking_a_train_selects_the_train(self, game: Game):
        create_objects(
            game.grid,
            """
            . M . F .

            .-S-.-S-.
            """,
        )
        game._create_train(*game.grid.station_from_position.values())
        game.gui.disable()
        game.gui.mode = Mode.SELECT
        train = game.trains[0]
        train.selected = False

        game.on_left_click(45, 15)

        assert train.selected


class TestSignals:
    def test_hovering_over_rail_in_signal_mode_shows_signal_outline(self, game: Game):
        create_objects(
            game.grid,
            """
            .-.
            """,
        )
        game.gui.mode = Mode.SIGNAL
        game.gui.disable()

        assert len(game.drawer.signals_being_built_shape_element_list) == 0

        game.on_mouse_motion(30, 15, 0, 0)

        assert len(game.drawer.signals_being_built_shape_element_list) == 2

    def test_remove_signal_outline_when_hovering_elsewhere(self, game: Game):
        create_objects(
            game.grid,
            """
            .-.
            """,
        )
        game.gui.mode = Mode.SIGNAL
        game.gui.disable()

        game.on_mouse_motion(30, 15, 0, 0)

        assert len(game.drawer.signals_being_built_shape_element_list) == 2

        game.on_mouse_motion(60, 15, 0, 0)

        assert len(game.drawer.signals_being_built_shape_element_list) == 0

    def test_creating_signal_creates_two_signal_blocks(self, game: Game):
        create_objects(
            game.grid,
            """
            .-.h.-.
            """,
        )
        game.grid.toggle_signals_at_click_position(60, 15)
        # Sort the blocks so that the test becomes predictable
        blocks = sorted(
            game.signal_controller._signal_blocks, key=lambda b: sorted(b.positions)[0]
        )
        assert len(blocks) == 2
        assert blocks[0].positions == frozenset({Vec2(0, 0), Vec2(1, 0)})
        assert blocks[1].positions == frozenset({Vec2(2, 0), Vec2(3, 0)})

    def test_clicking_grid_in_signal_mode_creates_signal(self, game: Game):
        create_objects(
            game.grid,
            """
        . M . F .

        .-S-.-S-.
        """,
        )
        assert len(game.grid.signals) == 0
        game.gui.disable()
        game.gui.mode = Mode.SIGNAL
        game.on_left_click(61, 1)
        assert len(game.grid.signals) == 2

    def test_clicking_signal_in_signal_mode_removes_signal(self, game: Game):
        create_objects(
            game.grid,
            """
        .h.
        """,
        )
        game.gui.disable()
        game.gui.mode = Mode.SIGNAL

        assert len(game.grid.signals) == 2

        game.on_left_click(45, 15)

        assert len(game.grid.signals) == 0

    def test_clicking_grid_in_signal_mode_when_no_rail_does_nothing(self, game: Game):
        """For code coverage."""
        game.gui.disable()
        game.gui.mode = Mode.SIGNAL
        game.on_left_click(61, 1)
        assert len(game.grid.signals) == 0

    def test_green_signal_colors_are_shown_for_adjacent_positions(self, game: Game):
        create_objects(
            game.grid,
            """
        .-.h.-.
        """,
        )
        assert all(
            signal.signal_color == SignalColor.GREEN
            for signal in game.grid.signals.values()
        )

    def test_signal_color_towards_block_with_train_is_red_and_towards_block_without_train_is_green(
        self, game: Game
    ):
        create_objects(
            game.grid,
            """
            . M . F . . .

            .-S-.-S-.h.-.
            """,
        )
        train = game._create_train(*game.grid.station_from_position.values())

        signal_to_the_west = game.grid.signals[(Vec2(4, 0), Rail(4, 0, 5, 0))]
        signal_to_the_east = game.grid.signals[(Vec2(5, 0), Rail(4, 0, 5, 0))]

        assert signal_to_the_west.signal_color == SignalColor.GREEN
        assert signal_to_the_east.signal_color == SignalColor.GREEN

        while check(train.speed == 0.0):
            game.on_update(1 / 60)

        assert signal_to_the_west.signal_color == SignalColor.GREEN
        assert signal_to_the_east.signal_color == SignalColor.RED

    def test_signal_is_green_when_rail_loop(self, game: Game):
        create_objects(
            game.grid,
            r"""
            . .-. .
             /   \
            . . . .
            |     |
            . . . .
             \   /
            . .h. .
            """,
        )

        game.signal_controller._update_signals()
        assert all(
            signal.signal_color == SignalColor.GREEN
            for signal in game.grid.signals.values()
        )

    def test_clicking_signal_in_destroy_mode_destroys_signal(
        self,
        game,
    ):
        create_objects(
            game.grid,
            """
        . M . F .

        .-Sh.-S-.
        """,
        )
        game.gui.mode = Mode.DESTROY

        assert len(game.grid.signals) == 2

        game.on_mouse_press(x=60, y=15, button=arcade.MOUSE_BUTTON_LEFT, modifiers=0)
        game.on_left_click(x=61, y=1)

        assert len(game.grid.signals) == 0

    def test_destroying_rail_resets_signal_blocks(
        self,
        game: Game,
    ):
        """Removing a rail splits two signal blocks into three."""
        create_objects(
            game.grid,
            """
            . M . F . .

            .-S-.-S-.h.-
            """,
        )
        assert len(game.signal_controller._signal_blocks) == 2

        game.grid.remove_rail(Vec2(2, 0))

        assert len(game.signal_controller._signal_blocks) == 3

    def test_destroying_rail_removes_rail_from_drawer(
        self,
        game: Game,
    ):
        game.gui.disable()
        game.gui.mode = Mode.RAIL
        game.on_mouse_press(15, 15, arcade.MOUSE_BUTTON_LEFT, 0)
        game.on_mouse_motion(45, 15, 30, 0)
        game.on_mouse_release(15, 15, arcade.MOUSE_BUTTON_LEFT, 0)

        assert len(game.drawer._rail_shape_list) == 12

        game.gui.mode = Mode.DESTROY
        game.on_left_click(15, 15)

        assert len(game.drawer._rail_shape_list) == 0

    def test_adding_rail_resets_signal_blocks(
        self,
        game: Game,
    ):
        create_objects(
            game.grid,
            """
            . M . F . .

            .-S-.-S-.h.-
            """,
        )
        game.grid.remove_rail(Vec2(2, 0))

        assert len(game.signal_controller._signal_blocks) == 3

        game.grid.create_rail({Rail(1, 0, 2, 0), Rail(2, 0, 3, 0)})

        assert len(game.signal_controller._signal_blocks) == 2

    def test_adding_adjacent_signals_does_not_hang_application(
        self,
        game: Game,
    ):
        create_objects(
            game.grid,
            """
            . M . . F .

            .-S-s-s-S-.-
            """,
        )


class TestTrainMovingAroundSignals:
    def test_train_chooses_green_route(self, game: Game):
        create_objects(
            game.grid,
            r"""
            .-.-.-.-.-.-.
            v           v
            Sh.-S-.-S-.hS

            M . M . F . F
            """,
        )
        stations = sorted(
            game.grid.station_from_position.values(),
            key=lambda station: station.positions[0],
        )
        game._create_train(stations[1], stations[2])
        train = game._create_train(stations[0], stations[3])

        while check(train.speed == 0.0):
            game.on_update(1 / 60)
        game.on_update(1 / 60)

        # Train chooses north route
        assert train.y > 1

    def test_if_a_train_is_destroyed_the_signals_become_green(self, game: Game):
        create_objects(
            game.grid,
            """
            . M . F .

            .-S-.-S-.
            """,
        )
        train = game._create_train(*game.grid.station_from_position.values())

        while check(train.speed == 0.0):
            game.on_update(1 / 60)

        # Currently, the block can be reserved either by the train or
        # one of its wagons
        train_and_wagon_ids = {id(train)} | {id(wagon) for wagon in train.wagons}
        assert (
            game.signal_controller._signal_blocks[0].reserved_by in train_and_wagon_ids
        )

        train.destroy()

        assert game.signal_controller._signal_blocks[0].reserved_by is None


class TestReserveAndUnreserveRail:
    def test_train_reserves_block_when_moving(self, game: Game):
        """Sends a train right and asserts that it stops reserving the first block
        and begins to reserve the other instead."""
        create_objects(
            game.grid,
            """
            . M . F .

            .-S-.-S-.
            """,
        )
        train = game._create_train(*game.grid.station_from_position.values())
        while check(train.speed == 0.0):
            game.on_update(1 / 60)

        assert game.signal_controller._signal_blocks[0].reserved_by == id(train)

    def test_a_train_with_a_single_wagon_reserves_both_blocks_when_leaving(
        self, game: Game
    ):
        """Sends a train right and asserts that eventually it reserves both blocks"""
        create_objects(
            game.grid,
            """
            . M . F .

            .-S-.hS-.
            """,
        )
        train = game._create_train(*game.grid.station_from_position.values())
        game.on_update(1 / 60)
        left_signal_block = game.signal_controller._signal_block_from_position[
            Vec2(1, 0)
        ]
        right_signal_block = game.signal_controller._signal_block_from_position[
            Vec2(4, 0)
        ]
        assert left_signal_block.reserved_by == id(train)
        while check(not right_signal_block.reserved_by):
            game.on_update(1 / 60)

        assert left_signal_block.reserved_by == id(train)
        assert right_signal_block.reserved_by == id(train)

    def test_a_train_with_one_wagon_eventually_unreserves_first_block(self, game: Game):
        create_objects(
            game.grid,
            """
            . M . . F .

            .-Sh.-.-S-.
            """,
        )
        train = game._create_train(*game.grid.station_from_position.values())
        game.on_update(1 / 60)
        left_signal_block = game.signal_controller._signal_block_from_position[
            Vec2(1, 0)
        ]
        right_signal_block = game.signal_controller._signal_block_from_position[
            Vec2(4, 0)
        ]
        while check(left_signal_block.reserved_by == id(train)):
            game.on_update(1 / 60)

        assert right_signal_block.reserved_by == id(train)

    def test_a_train_with_one_wagon_can_reserve_two_signal_blocks(self, game: Game):
        """Sends a train right and asserts that it eventually reserves both blocks"""
        create_objects(
            game.grid,
            """
            . M . F .

            .-S-.hS-.
            """,
        )
        train = game._create_train(*game.grid.station_from_position.values())

        # Sort signal blocks by x position, so that signal_blocks[0] is the western etc
        signal_blocks = sorted(
            game.signal_controller._signal_blocks,
            key=lambda b: sorted(b.positions)[0].x,
        )

        while check(train.speed == 0.0):
            game.on_update(1 / 60)

        assert signal_blocks[0].reserved_by == id(train)

        while check(not signal_blocks[1].reserved_by):
            game.on_update(1 / 60)

        assert signal_blocks[1].reserved_by == signal_blocks[0].reserved_by == id(train)


class TestPlayer:
    def test_grid_is_enlarged_when_leveling_up(self, game: Game):
        assert game.grid.left == -1
        assert game.grid.right == GRID_WIDTH_CELLS + 1
        game.player.money = 10
        assert game.grid.left == -2
        assert game.grid.right == GRID_WIDTH_CELLS + 2


class TestCreateWagon:
    def test_failure_shows_toast(self, game: Game):
        create_objects(
            game.grid,
            """
            . M . F .

            .-S-.-S-.
            """,
        )
        train = game._create_train(*game.grid.station_from_position.values())
        train.selected = True

        assert game.gui._toast_time_left == 0.0
        game._create_wagon_for_selected_train()
        assert game.gui._toast_time_left == 3.0

    def test_success(self, game: Game):
        create_objects(
            game.grid,
            """
            . M . . . F . .

            .-S-S-S-.-S-S-S-.
            """,
        )
        station1 = game.grid.get_station(1, 0)
        station2 = game.grid.get_station(5, 0)
        assert station1
        assert station2
        train = game._create_train(station1, station2)
        train.selected = True

        assert len(train.wagons) == 1
        game._create_wagon_for_selected_train()
        assert len(train.wagons) == 2


def test_destroy_train_button(game: Game):
    create_objects(
        game.grid,
        """
        . M . F .

        .-S-.-S-.
        """,
    )
    train = game._create_train(*game.grid.station_from_position.values())
    train.selected = True

    assert len(game.trains) == 1
    game.gui.boxes["DESTROY\nTRAIN"].click()
    assert len(game.trains) == 0
