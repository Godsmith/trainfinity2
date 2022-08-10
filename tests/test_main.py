import arcade
import pytest
from constants import SECONDS_BETWEEN_IRON_CREATION
from main import MyGame, Mode, Train, TrainPlacementMode
from model import Player, Rail, Station, Mine, Factory, Train, Water
from pyglet.math import Vec2
from pytest import approx
import time


@pytest.fixture(autouse=True, scope="session")
def common_game() -> MyGame:
    return MyGame(visible=False)


@pytest.fixture
def game(common_game: MyGame) -> MyGame:
    common_game.setup(terrain=False)
    common_game.grid.water = {}
    common_game.grid.mines = {}
    common_game.grid.factories = {}
    return common_game


@pytest.fixture
def game_with_train(game: MyGame) -> MyGame:
    """
     M F
    =S=S=
    """
    game.grid.rails = [
        Rail(0, 0, 30, 0),
        Rail(30, 0, 60, 0),
        Rail(60, 0, 90, 0),
        Rail(90, 0, 120, 0),
    ]
    game.grid._create_mine(30, 30)
    game.grid._create_factory(90, 30)
    station1 = game.grid._create_station(30, 0)
    station2 = game.grid._create_station(90, 0)
    game._create_train(game.grid.rails[1:3], station1, station2)
    return game


def test_draw(game_with_train: MyGame):
    # Mainly for code coverage
    game_with_train.on_draw()


class TestClicks:
    def test_create_click(self, game: MyGame, monkeypatch):
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

        # TODO: forgot assert here
        assert game.camera

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


class TestGrid:
    def test_horizontal_rail_being_built(self, game: MyGame):
        game.on_mouse_press(x=90, y=90, button=arcade.MOUSE_BUTTON_LEFT, modifiers=0)
        game.on_mouse_motion(x=120, y=90, dx=30, dy=0)

        assert game.grid.rails_being_built == [Rail(90, 90, 120, 90)]

    def test_vertical_rail_being_built(self, game: MyGame):
        game.on_mouse_press(x=90, y=90, button=arcade.MOUSE_BUTTON_LEFT, modifiers=0)
        game.on_mouse_motion(x=90, y=120, dx=0, dy=30)

        assert game.grid.rails_being_built == [Rail(90, 90, 90, 120)]

    def test_diagonal_rail_being_built(self, game: MyGame):
        game.on_mouse_press(x=90, y=90, button=arcade.MOUSE_BUTTON_LEFT, modifiers=0)
        game.on_mouse_motion(x=120, y=120, dx=30, dy=30)

        assert game.grid.rails_being_built == [Rail(90, 90, 120, 120)]

    def test_non_straight_rail_being_built(self, game: MyGame):
        game.on_mouse_press(x=90, y=90, button=arcade.MOUSE_BUTTON_LEFT, modifiers=0)
        game.on_mouse_motion(x=120, y=150, dx=30, dy=60)

        assert game.grid.rails_being_built == [
            Rail(x1=90, y1=90, x2=90, y2=120),
            Rail(x1=90, y1=120, x2=120, y2=150),
        ]

    def test_built_rail(self, game: MyGame):
        game.on_mouse_press(x=100, y=100, button=arcade.MOUSE_BUTTON_LEFT, modifiers=0)
        game.on_mouse_motion(x=130, y=100, dx=30, dy=0)
        game.on_mouse_release(
            x=130, y=100, button=arcade.MOUSE_BUTTON_LEFT, modifiers=0
        )

        assert len(game.grid.rails_being_built) == 0
        assert len(game.grid.rails) == 1

    def test_cannot_build_rail_in_illegal_position(self, game: MyGame):
        game.grid.water = {Vec2(90, 90): Water(90, 90)}

        game.on_mouse_press(x=100, y=100, button=arcade.MOUSE_BUTTON_LEFT, modifiers=0)
        game.on_mouse_motion(x=130, y=100, dx=30, dy=0)
        game.on_mouse_release(
            x=130, y=100, button=arcade.MOUSE_BUTTON_LEFT, modifiers=0
        )

        assert len(game.grid.rails) == 0

    def drag_one_tile_outside_grid(self, game: MyGame):
        game.on_mouse_press(x=15, y=15, button=arcade.MOUSE_BUTTON_LEFT, modifiers=0)
        game.on_mouse_motion(x=-15, y=15, dx=-30, dy=0)
        game.on_mouse_release(x=-15, y=15, button=arcade.MOUSE_BUTTON_LEFT, modifiers=0)

    def test_cannot_build_rail_outside_grid(self, game: MyGame):
        self.drag_one_tile_outside_grid(game)

        assert len(game.grid.rails) == 0

    def test_can_build_rail_outside_grid_when_grid_has_enlarged(self, game: MyGame):
        game.grid.enlarge_grid()
        self.drag_one_tile_outside_grid(game)

        assert len(game.grid.rails) == 1

    def test_building_horizontal_station(self, game: MyGame):
        mine = game.grid._create_mine(30, 30)
        game.on_mouse_press(x=15, y=15, button=arcade.MOUSE_BUTTON_LEFT, modifiers=0)
        game.on_mouse_motion(x=75, y=15, dx=60, dy=0)
        game.on_mouse_release(x=75, y=15, button=arcade.MOUSE_BUTTON_LEFT, modifiers=0)

        assert game.grid.stations == {Vec2(30, 0): Station(30, 0, mine)}

    def test_building_vertical_station(self, game: MyGame):
        factory = game.grid._create_factory(30, 30)
        game.on_mouse_press(x=15, y=15, button=arcade.MOUSE_BUTTON_LEFT, modifiers=0)
        game.on_mouse_motion(x=15, y=75, dx=0, dy=60)
        game.on_mouse_release(x=15, y=75, button=arcade.MOUSE_BUTTON_LEFT, modifiers=0)

        assert game.grid.stations == {Vec2(0, 30): Station(0, 30, factory)}


@pytest.fixture
def game_with_factory_and_mine(game):
    """
     M F
    =S=S=
    """
    game.grid._create_mine(30, 30)
    game.grid._create_factory(90, 30)
    game.grid._create_rail(
        [
            Rail(0, 0, 30, 0),
            Rail(30, 0, 60, 0),
            Rail(60, 0, 90, 0),
            Rail(90, 0, 120, 0),
        ]
    )
    for x, y in ((30, 0), (90, 0)):
        game.grid._create_station(x, y)

    return game


class TestGui:
    def test_game_starts_in_rail_mode(self, game: MyGame):
        assert game.gui.mode == Mode.RAIL

    def test_clicking_bottom_left_corner_switches_to_select_mode(self, game: MyGame):
        game.on_left_click(15, 15)
        assert game.gui.mode == Mode.SELECT


class TestTrain:
    def test_clicking_nothing_in_train_mode_does_nothing(
        self, game_with_factory_and_mine: MyGame
    ):
        """Mainly for code coverage"""
        # game = game_with_factory_and_mine
        # game.gui.mode = Mode.TRAIN
        # game.gui.disable()

        # game.on_left_click(100, 100)

    def test_clicking_station_in_train_mode_changes_train_placement_mode(
        self, game_with_factory_and_mine: MyGame
    ):
        game = game_with_factory_and_mine
        game.gui.mode = Mode.TRAIN
        game.gui.disable()

        assert game.train_placement_mode == TrainPlacementMode.FIRST_STATION

        # TODO: it would be nice for readability if I could just say station.click() here.
        # Click first station
        game.on_left_click(30, 0)

        assert game.train_placement_mode == TrainPlacementMode.SECOND_STATION

    def test_clicking_station_in_train_mode_highlights_station(
        self, game_with_factory_and_mine: MyGame
    ):
        game = game_with_factory_and_mine
        game.gui.mode = Mode.TRAIN
        game.gui.disable()

        assert len(game.drawer.highlight_shape_element_list) == 0

        # Click first station
        game.on_left_click(30, 0)

        assert len(game.drawer.highlight_shape_element_list) == 1

    def test_hovering_over_connected_station_highlights_route(
        self, game_with_factory_and_mine: MyGame
    ):
        game = game_with_factory_and_mine
        game.gui.mode = Mode.TRAIN
        game.gui.disable()

        # Click first station
        game.on_left_click(30, 0)
        # Hover over next station
        game.on_mouse_motion(90, 0, 0, 0)

        assert len(game.drawer.highlight_shape_element_list) == 3

    def test_clicking_two_connected_stations_creates_train(
        self, game_with_factory_and_mine: MyGame
    ):
        """
        The grid is lain out as follows:

         M F
        =S=S=

        When clicking the two stations, a train shall be created.
        """
        game = game_with_factory_and_mine
        game.gui.mode = Mode.TRAIN

        # TODO: it would be nice for readability if I could just say station.click() here.
        # Click first station
        game.on_left_click(30, 0)
        # Click next station
        game.on_left_click(90, 0)

        assert len(game.trains) == 1

    def test_clicking_two_connected_stations_removes_highlight(
        self, game_with_factory_and_mine: MyGame
    ):
        game = game_with_factory_and_mine
        game.gui.mode = Mode.TRAIN

        # TODO: it would be nice for readability if I could just say station.click() here.
        # Click first station
        game.on_left_click(30, 0)
        # Click next station
        game.on_left_click(90, 0)

        assert len(game.drawer.highlight_shape_element_list) == 0

    def test_clicking_two_unconnected_stations_does_not_create_train(
        self, game_with_factory_and_mine: MyGame
    ):
        """
        Create a new station on top, like this:

        =S=
         M F
        =S=S=

        When clicking two unconnected stations, the TrainPlacementMode goes back to FIRST_STATION again.
        """
        game = game_with_factory_and_mine
        game.gui.mode = Mode.TRAIN

        game.grid.rails.extend(
            [
                Rail(0, 90, 30, 90),
                Rail(30, 90, 60, 90),
            ]
        )
        game.grid.stations[Vec2(30, 90)] = Station(
            30, 90, game.grid.mines[Vec2(30, 30)]
        )

        # TODO: it would be nice for readability if I could just say station.click() here.
        # Click first station
        game.on_left_click(30, 0)
        # Click next station
        game.on_left_click(30, 90)

        assert len(game.trains) == 0
        assert game.train_placement_mode == TrainPlacementMode.FIRST_STATION

    def test_create_two_trains(self, game_with_factory_and_mine: MyGame):
        """
        The grid is lain out as follows:

         M F
        =S=S=

        When clicking the two stations, a train shall be created.
        """
        game = game_with_factory_and_mine
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

        assert len(game.trains) == 2


def test_clicking_position_in_destroy_mode_destroys_station_and_rail(
    game_with_factory_and_mine,
):
    game = game_with_factory_and_mine
    game.gui.mode = Mode.DESTROY

    assert len(game.grid.stations) == 2
    assert len(game.grid.rails) == 4

    game.on_mouse_press(x=45, y=15, button=arcade.MOUSE_BUTTON_LEFT, modifiers=0)
    game.on_mouse_motion(x=46, y=15, dx=1, dy=30)

    assert len(game.grid.stations) == 1
    assert len(game.grid.rails) == 2


def test_destroying_rail_destroys_train(game_with_train):
    game = game_with_train
    game.gui.mode = Mode.DESTROY

    assert len(game.trains) == 1

    game.on_mouse_press(x=75, y=15, button=arcade.MOUSE_BUTTON_LEFT, modifiers=0)
    game.on_mouse_motion(x=76, y=15, dx=1, dy=0)

    assert len(game.trains) == 0


def test_iron_is_regularly_added_to_mines(game_with_factory_and_mine):
    game = game_with_factory_and_mine
    # Start just before creating a new iron
    game.iron_counter = SECONDS_BETWEEN_IRON_CREATION - 0.00001

    game.on_update(1 / 60)

    assert game.grid.mines[Vec2(30, 30)].iron == 1
    assert (
        len(game.drawer.iron_shape_element_list) == 2
    )  # One for the interior, one for the frame


def test_trains_are_moved_in_on_update(game_with_train):
    # For code coverage
    game_with_train.on_update(1 / 60)


def test_fps_is_updated_every_second(game: MyGame):
    # For code coverage
    game.seconds_since_last_frame_count_display = 0.99

    game.on_update(1 / 60)


def test_train_picks_up_iron_from_mine(game_with_train: MyGame):
    """
     M F
    =S=S=
    """
    mine = game_with_train.grid.mines[Vec2(30, 30)]
    train = game_with_train.trains[0]
    mine.add_iron()
    train.x = 30
    train.target_x = 30

    game_with_train.on_update(1 / 60)

    assert mine.iron == 0
    assert train.iron == 1


def test_train_delivers_iron_to_factory_gives_score(game_with_train: MyGame):
    """
     M F
    =S=S=
    """
    train = game_with_train.trains[0]
    train.iron = 1
    train.x = 90
    train.target_x = 90

    game_with_train.on_update(1 / 60)

    assert train.iron == 0
    assert game_with_train.player.score == 1


def test_on_resize(game):
    # For code coverage
    game.on_resize(800, 600)


class TestSelect:
    def test_clicking_outside_all_trains_deselects_all_trains(self, game_with_train):
        game_with_train.gui.disable()
        game_with_train.gui.mode = Mode.SELECT
        train = game_with_train.trains[0]
        train.selected = True

        game_with_train.on_left_click(500, 500)

        assert not train.selected

    def test_clicking_a_train_selects_the_train(self, game_with_train):
        game_with_train.gui.disable()
        game_with_train.gui.mode = Mode.SELECT
        train = game_with_train.trains[0]
        train.selected = False

        game_with_train.on_left_click(45, 15)

        assert train.selected
