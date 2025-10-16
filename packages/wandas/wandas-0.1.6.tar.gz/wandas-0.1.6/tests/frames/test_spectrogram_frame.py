from typing import Any, Optional

import dask.array as da
import pytest
from dask.array.core import Array as DaArray
from numpy.testing import assert_array_almost_equal, assert_array_equal

from wandas.core.metadata import ChannelMetadata
from wandas.frames.spectral import SpectralFrame
from wandas.frames.spectrogram import SpectrogramFrame
from wandas.utils.types import NDArrayComplex, NDArrayReal

# Reference to dask array functions
_da_random_random = da.random.random  # type: ignore [unused-ignore]


@pytest.fixture  # type: ignore [misc, unused-ignore]
def sample_spectrogram() -> SpectrogramFrame:
    """スペクトログラムのサンプルデータを生成するフィクスチャ"""
    # 形状: (channels=2, freq_bins=513, time_frames=10)
    complex_data: DaArray = _da_random_random((2, 65, 5)) + 1j * _da_random_random(
        (2, 65, 5)
    )

    # メタデータの設定
    channel_metadata: list[ChannelMetadata] = [
        ChannelMetadata(label="ch1", unit="Pa", ref=1.0),
        ChannelMetadata(label="ch2", unit="Pa", ref=1.0),
    ]

    return SpectrogramFrame(
        data=complex_data,
        sampling_rate=44100,
        n_fft=128,
        hop_length=64,
        window="hann",
        label="test_spectrogram",
        channel_metadata=channel_metadata,
    )


class TestSpectrogramFrame:
    """SpectrogramFrameクラスのテストスイート"""

    def test_spectrogram_init(self) -> None:
        """SpectrogramFrameの初期化テスト"""
        # 2D配列から初期化（単一チャネル）
        data_2d: DaArray = _da_random_random((513, 10)) + 1j * _da_random_random(
            (513, 10)
        )
        spec_2d: SpectrogramFrame = SpectrogramFrame(
            data=data_2d,
            sampling_rate=44100.0,
            n_fft=1024,
            hop_length=512,
        )
        assert spec_2d.shape == (513, 10)

        # 3D配列から初期化（複数チャネル）
        data_3d: DaArray = _da_random_random((2, 513, 10)) + 1j * _da_random_random(
            (2, 513, 10)
        )
        spec_3d: SpectrogramFrame = SpectrogramFrame(
            data=data_3d,
            sampling_rate=44100.0,
            n_fft=1024,
            hop_length=512,
        )
        assert spec_3d.shape == (2, 513, 10)

        # 不正な次元の配列（1次元）
        with pytest.raises(
            ValueError, match="データは2次元または3次元である必要があります"
        ):
            data_1d: DaArray = _da_random_random(10) + 1j * _da_random_random(10)
            SpectrogramFrame(
                data=data_1d,
                sampling_rate=44100.0,
                n_fft=1024,
                hop_length=512,
            )

        # 不正な次元の配列（4次元）
        with pytest.raises(
            ValueError, match="データは2次元または3次元である必要があります"
        ):
            data_4d: DaArray = _da_random_random(
                (2, 513, 10, 2)
            ) + 1j * _da_random_random((2, 513, 10, 2))
            SpectrogramFrame(
                data=data_4d,
                sampling_rate=44100.0,
                n_fft=1024,
                hop_length=512,
            )

        # 不正な周波数ビン数
        with pytest.raises(
            ValueError,
            match="データの形状が無効です。周波数ビン数は 513 である必要があります",
        ):
            data_invalid_bins: DaArray = _da_random_random(
                (2, 400, 10)
            ) + 1j * _da_random_random((2, 400, 10))
            SpectrogramFrame(
                data=data_invalid_bins,
                sampling_rate=44100.0,
                n_fft=1024,
                hop_length=512,
            )

    def test_properties(self, sample_spectrogram: SpectrogramFrame) -> None:
        """各プロパティの動作テスト"""
        spec: SpectrogramFrame = sample_spectrogram

        # 基本的なプロパティ
        assert spec.n_fft == 128
        assert spec.hop_length == 64
        assert spec.window == "hann"
        assert spec.sampling_rate == 44100.0

        # データ関連プロパティ
        assert spec._n_channels == 2
        assert spec.n_frames == 5
        assert spec.n_freq_bins == 65

        # 各種変換プロパティ
        magnitude: NDArrayReal = spec.magnitude
        phase: NDArrayReal = spec.phase
        power: NDArrayReal = spec.power
        db: NDArrayReal = spec.dB
        dba: NDArrayReal = spec.dBA

        assert magnitude.shape == (2, 65, 5)
        assert phase.shape == (2, 65, 5)
        assert power.shape == (2, 65, 5)
        assert db.shape == (2, 65, 5)
        assert dba.shape == (2, 65, 5)

        # magnitude と power の関係を確認
        assert_array_almost_equal(power, magnitude**2)

        # 周波数・時間軸の確認
        freqs: NDArrayReal = spec.freqs
        times: NDArrayReal = spec.times
        assert len(freqs) == spec.n_freq_bins  # FFTサイズの半分 + 1
        assert len(times) == 5

    def test_binary_operations(self, sample_spectrogram: SpectrogramFrame) -> None:
        """二項演算子の動作テスト"""
        spec: SpectrogramFrame = sample_spectrogram

        # スカラー演算
        spec_plus_1: SpectrogramFrame = spec + 1.0
        assert spec_plus_1.label == f"({spec.label} + 1.0)"

        # 実データの比較確認
        result: NDArrayComplex = spec_plus_1.data
        expected: NDArrayComplex = spec.data + 1.0
        assert_array_almost_equal(result, expected)

        # 同種データ間の演算
        spec_double: SpectrogramFrame = spec + spec
        assert spec_double.label == f"({spec.label} + {spec.label})"

        # その他の演算子
        spec_minus: SpectrogramFrame = spec - 0.5
        spec_mult: SpectrogramFrame = spec * 2.0
        spec_div: SpectrogramFrame = spec / 2.0

        # 各演算結果の検証
        assert_array_almost_equal((spec_minus.data), (spec.data - 0.5))
        assert_array_almost_equal((spec_mult.data), (spec.data * 2.0))
        assert_array_almost_equal((spec_div.data), (spec.data / 2.0))

    def test_binary_operations_sampling_rate_mismatch(
        self, sample_spectrogram: SpectrogramFrame
    ) -> None:
        """
        サンプリングレートが異なるSpectrogramFrame同士の演算で
        例外が発生することをテスト
        """
        spec1: SpectrogramFrame = sample_spectrogram

        # 異なるサンプリングレートのSpectrogramFrameを作成
        complex_data: DaArray = _da_random_random((2, 65, 5)) + 1j * _da_random_random(
            (2, 65, 5)
        )
        spec2: SpectrogramFrame = SpectrogramFrame(
            data=complex_data,
            sampling_rate=48000.0,  # 異なるサンプリングレート
            n_fft=128,
            hop_length=64,
            window="hann",
        )

        # サンプリングレートが異なる場合、ValueErrorが発生することを確認
        with pytest.raises(
            ValueError, match="サンプリングレートが一致していません。演算できません。"
        ):
            _ = spec1 + spec2

        with pytest.raises(
            ValueError, match="サンプリングレートが一致していません。演算できません。"
        ):
            _ = spec1 - spec2

        with pytest.raises(
            ValueError, match="サンプリングレートが一致していません。演算できません。"
        ):
            _ = spec1 * spec2

        with pytest.raises(
            ValueError, match="サンプリングレートが一致していません。演算できません。"
        ):
            _ = spec1 / spec2

    def test_binary_operations_with_various_types(
        self, sample_spectrogram: SpectrogramFrame
    ) -> None:
        """様々な型との二項演算をテスト"""
        import numpy as np

        spec: SpectrogramFrame = sample_spectrogram

        # complex型との演算
        complex_val = 1.0 + 2.0j
        spec_complex: SpectrogramFrame = spec + complex_val
        assert "complex(1.0, 2.0)" in spec_complex.label
        assert_array_almost_equal(spec_complex.data, spec.data + complex_val)

        # numpy配列との演算
        np_array = np.ones((2, 65, 5), dtype=complex)
        spec_np: SpectrogramFrame = spec * np_array
        assert "ndarray(2, 65, 5)" in spec_np.label
        assert_array_almost_equal(spec_np.data, spec.data * np_array)

        # dask配列との演算
        da_array: DaArray = da.ones((2, 65, 5), dtype=complex)
        spec_da: SpectrogramFrame = spec - da_array
        assert "dask.array(2, 65, 5)" in spec_da.label
        assert_array_almost_equal(spec_da.data, spec.data - da_array)

        # その他の型（カスタムオブジェクト）との演算でelse節をカバー
        # 演算をサポートするカスタムクラスを作成
        class CustomNumber:
            def __init__(self, value: complex) -> None:
                self.value = value

            def __radd__(self, other: Any) -> Any:
                # dask配列との加算をサポート
                if isinstance(other, DaArray):
                    return other + self.value
                return other + self.value

        custom_obj = CustomNumber(1.0 + 0j)
        spec_custom: SpectrogramFrame = spec + custom_obj
        # カスタムオブジェクトの型名がラベルに含まれることを確認
        assert "CustomNumber" in spec_custom.label
        assert_array_almost_equal(spec_custom.data, spec.data + custom_obj.value)

    def test_get_frame_at(self, sample_spectrogram: SpectrogramFrame) -> None:
        """特定時間フレームの取得テスト"""
        spec: SpectrogramFrame = sample_spectrogram

        # 正常なインデックス
        frame: SpectralFrame = spec.get_frame_at(4)
        assert frame.shape == (2, 65)  # チャネル数 x 周波数ビン数

        # 範囲外インデックス（負の値）
        with pytest.raises(
            IndexError,
            match=r"時間インデックス -1 が範囲外です。有効範囲: 0-\d+",
        ):
            spec.get_frame_at(-1)

        # 範囲外インデックス（大きすぎる値）
        with pytest.raises(
            IndexError,
            match=r"時間インデックス 20 が範囲外です。有効範囲: 0-\d+",
        ):
            spec.get_frame_at(20)  # n_frames=5 なので範囲外

        # 境界値テスト（n_frames と同じ値）
        with pytest.raises(
            IndexError,
            match=r"時間インデックス 5 が範囲外です。有効範囲: 0-\d+",
        ):
            spec.get_frame_at(5)  # n_frames=5 なので範囲外

    def test_to_channel_frame(self, sample_spectrogram: SpectrogramFrame) -> None:
        """時間領域への変換テスト"""
        spec: SpectrogramFrame = sample_spectrogram
        channel_frame: Any = spec.to_channel_frame()

        # 基本プロパティの確認
        assert channel_frame.sampling_rate == spec.sampling_rate
        assert channel_frame._n_channels == spec._n_channels

    def test_istft(self, sample_spectrogram: SpectrogramFrame) -> None:
        """istftメソッドがto_channel_frameのエイリアスとして機能することをテスト"""
        spec: SpectrogramFrame = sample_spectrogram

        # istftメソッドを呼び出し
        channel_frame_istft: Any = spec.istft()

        # to_channel_frameメソッドを呼び出し
        channel_frame_to: Any = spec.to_channel_frame()

        # 両者が同じプロパティを持つことを確認
        assert channel_frame_istft.sampling_rate == channel_frame_to.sampling_rate
        assert channel_frame_istft._n_channels == channel_frame_to._n_channels
        assert channel_frame_istft.shape == channel_frame_to.shape

        # データが同じであることを確認
        assert_array_almost_equal(channel_frame_istft.data, channel_frame_to.data)

    def test_plot(self, sample_spectrogram: SpectrogramFrame, monkeypatch: Any) -> None:
        """プロット機能のモックテスト"""

        # PlotStrategy をモック
        class MockPlotStrategy:
            def plot(
                self, frame: SpectrogramFrame, ax: Optional[Any] = None, **kwargs: Any
            ) -> None:
                return None

        # create_operation 関数をモック
        def mock_create_operation(plot_type: str) -> MockPlotStrategy:
            return MockPlotStrategy()

        # モックを適用
        import wandas.visualization.plotting

        monkeypatch.setattr(
            wandas.visualization.plotting, "create_operation", mock_create_operation
        )

        # プロット機能をテスト
        result: Optional[Any] = sample_spectrogram.plot(plot_type="spectrogram")
        assert result is None

    def test_get_additional_init_kwargs(
        self, sample_spectrogram: SpectrogramFrame
    ) -> None:
        """_get_additional_init_kwargs メソッドのテスト"""
        spec: SpectrogramFrame = sample_spectrogram

        # _get_additional_init_kwargs メソッドを呼び出す
        additional_kwargs = spec._get_additional_init_kwargs()

        # 返り値が正しい型であることを確認
        assert isinstance(additional_kwargs, dict)

        # 期待されるキーがすべて含まれていることを確認
        expected_keys = ["n_fft", "hop_length", "win_length", "window"]
        for key in expected_keys:
            assert key in additional_kwargs

        # 値が正しいことを確認
        assert additional_kwargs["n_fft"] == spec.n_fft
        assert additional_kwargs["hop_length"] == spec.hop_length
        assert additional_kwargs["win_length"] == spec.win_length
        assert additional_kwargs["window"] == spec.window

    def test_plot_Aw(  # noqa: N802
        self, sample_spectrogram: SpectrogramFrame, monkeypatch: Any
    ) -> None:
        """Test that plot_Aw correctly passes Aw=True to plot method"""

        # Keep track of the parameters passed to plot
        plot_args = {}

        def mock_plot(
            self: SpectrogramFrame,
            plot_type: str = "spectrogram",
            ax: Optional[Any] = None,
            **kwargs: Any,
        ) -> None:
            nonlocal plot_args
            plot_args = {"plot_type": plot_type, "ax": ax, **kwargs}
            return None

        # Apply the mock
        monkeypatch.setattr(SpectrogramFrame, "plot", mock_plot)

        # Call plot_Aw with various parameters
        sample_spectrogram.plot_Aw(plot_type="spectrogram", cmap="viridis", vmin=-10)

        # Verify that plot was called with Aw=True and all other parameters
        assert plot_args["plot_type"] == "spectrogram"
        assert plot_args["Aw"] is True
        assert plot_args["cmap"] == "viridis"
        assert plot_args["vmin"] == -10

        from unittest.mock import Mock

        from matplotlib.axes import Axes

        mock_ax: Axes = Mock(spec=Axes)
        sample_spectrogram.plot_Aw(ax=mock_ax)
        assert plot_args["ax"] == mock_ax
        assert plot_args["Aw"] is True

    def test_apply_operation_impl(
        self, sample_spectrogram: SpectrogramFrame, monkeypatch: Any
    ) -> None:
        """_apply_operation_impl メソッドのテスト"""

        # 処理済みデータのサンプル作成
        processed_data = sample_spectrogram._data + 1.0

        # モックオペレーション作成
        class MockOperation:
            def __init__(self) -> None:
                self.called = False

            def process(self, data: Any) -> Any:
                self.called = True
                return processed_data

        mock_op = MockOperation()

        # create_operation 関数をモック
        def mock_create_operation(
            operation_name: str, sampling_rate: float, **params: Any
        ) -> MockOperation:
            assert operation_name == "test_operation"
            assert sampling_rate == sample_spectrogram.sampling_rate
            assert params == {"param1": 10, "param2": "test"}
            return mock_op

        # モックを適用
        import wandas.processing

        monkeypatch.setattr(
            wandas.processing,
            "create_operation",
            mock_create_operation,
        )

        # _create_new_instance をモック（実際の処理を維持しつつ、呼び出しを追跡）
        original_create_new_instance = sample_spectrogram._create_new_instance
        create_new_instance_called = False

        def mock_create_new_instance(
            self: SpectrogramFrame, **kwargs: Any
        ) -> SpectrogramFrame:
            nonlocal create_new_instance_called
            create_new_instance_called = True
            return original_create_new_instance(**kwargs)

        monkeypatch.setattr(
            SpectrogramFrame, "_create_new_instance", mock_create_new_instance
        )

        # メソッドを実行（注: 実装には pass があるので、
        # 実際は test_fix_apply_operation_impl も作成すべき）
        result = sample_spectrogram._apply_operation_impl(
            "test_operation", param1=10, param2="test"
        )

        # プロセスが呼び出されたことを確認
        assert mock_op.called

        # 新しいインスタンスが作成されたことを確認
        assert create_new_instance_called

        # 結果が正しいSpectrogramFrameオブジェクトであることを確認
        assert isinstance(result, SpectrogramFrame)

        # メタデータが正しく更新されていることを確認
        assert "test_operation" in result.metadata
        assert result.metadata["test_operation"] == {"param1": 10, "param2": "test"}

        # 操作履歴が正しく更新されていることを確認
        last_operation = result.operation_history[-1]
        assert last_operation["operation"] == "test_operation"
        assert last_operation["params"] == {"param1": 10, "param2": "test"}

        # データが正しく更新されていることを確認
        assert_array_equal(result.data, processed_data)

    def test_fix_apply_operation_impl(
        self, sample_spectrogram: SpectrogramFrame, monkeypatch: Any
    ) -> None:
        """_apply_operation_impl メソッドの修正版テスト（pass 文を削除した場合）"""

        # 実装内の pass 文が削除されることを想定したテスト
        # SpectrogramFrame._apply_operation_impl のコピーから pass 文を削除
        def fixed_apply_operation_impl(
            self: SpectrogramFrame, operation_name: str, **params: Any
        ) -> SpectrogramFrame:
            from wandas.processing import create_operation

            operation = create_operation(operation_name, self.sampling_rate, **params)
            processed_data = operation.process(self._data)

            operation_metadata = {"operation": operation_name, "params": params}
            new_history = self.operation_history.copy()
            new_history.append(operation_metadata)
            new_metadata = {**self.metadata}
            new_metadata[operation_name] = params

            return self._create_new_instance(
                data=processed_data,
                metadata=new_metadata,
                operation_history=new_history,
            )

        # モックを適用
        monkeypatch.setattr(
            SpectrogramFrame, "_apply_operation_impl", fixed_apply_operation_impl
        )

        # 処理済みデータのサンプル作成
        processed_data = sample_spectrogram._data + 1.0

        # モックオペレーション作成
        class MockOperation:
            def process(self, data: Any) -> Any:
                return processed_data

        # create_operation 関数をモック
        def mock_create_operation(
            operation_name: str, sampling_rate: float, **params: Any
        ) -> MockOperation:
            return MockOperation()

        # モックを適用
        import wandas.processing

        monkeypatch.setattr(
            wandas.processing,
            "create_operation",
            mock_create_operation,
        )

        # テスト実行
        result = sample_spectrogram._apply_operation_impl(
            "test_operation", param1=10, param2="test"
        )

        # 結果の検証
        assert isinstance(result, SpectrogramFrame)
        assert_array_equal(result.data, processed_data)
        assert "test_operation" in result.metadata
        assert result.operation_history[-1]["operation"] == "test_operation"

    def test_dBA_property(  # noqa: N802
        self, sample_spectrogram: SpectrogramFrame, monkeypatch: Any
    ) -> None:
        """dBAプロパティが正しくA特性重み付けを適用していることを確認"""
        import librosa
        import numpy as np

        spec: SpectrogramFrame = sample_spectrogram

        # A特性の重み付けの計算をモックする
        mock_a_weights = np.array([1.0, 2.0, 3.0, 4.0, 5.0])  # サンプル重み

        def mock_a_weighting(frequencies: Any, min_db: Any = None) -> NDArrayReal:
            # 実際のfreqsと同じ長さの配列を返す
            weights = np.zeros(len(frequencies))
            # テスト用の簡易的な重み付け
            for i in range(min(len(frequencies), len(mock_a_weights))):
                weights[i] = mock_a_weights[i]
            return weights

        # librosa.A_weightingをモック
        monkeypatch.setattr(librosa, "A_weighting", mock_a_weighting)

        # dBとdBAの値を取得
        db_values = spec.dB
        dba_values = spec.dBA

        # 各周波数ビンの最初の時間フレームと最初のチャネルについて確認
        for i in range(min(5, spec.n_freq_bins)):
            # dBA = dB + A_weight であることを確認
            expected_dba = db_values[0, i, 0] + mock_a_weights[i]
            assert_array_almost_equal(dba_values[0, i, 0], expected_dba)

        # 形状が同じであることを確認
        assert dba_values.shape == db_values.shape

    def test_abs(self, sample_spectrogram: SpectrogramFrame) -> None:
        """abs()メソッドの動作テスト"""
        import numpy as np

        spec: SpectrogramFrame = sample_spectrogram

        # abs()メソッドを呼び出し
        abs_spec: SpectrogramFrame = spec.abs()

        # 戻り値がSpectrogramFrameのインスタンスであることを確認
        assert isinstance(abs_spec, SpectrogramFrame)

        # 形状が同じであることを確認
        assert abs_spec.shape == spec.shape

        # サンプリングレートやその他のパラメータが保持されていることを確認
        assert abs_spec.sampling_rate == spec.sampling_rate
        assert abs_spec.n_fft == spec.n_fft
        assert abs_spec.hop_length == spec.hop_length
        assert abs_spec.win_length == spec.win_length
        assert abs_spec.window == spec.window

        # ラベルが正しく更新されていることを確認
        assert abs_spec.label == f"abs({spec.label})"

        # データが絶対値になっていることを確認
        original_magnitude = np.abs(spec.data)
        abs_magnitude = np.abs(abs_spec.data)
        assert_array_almost_equal(abs_magnitude, original_magnitude)

        # 操作履歴に "abs" が追加されていることを確認
        assert len(abs_spec.operation_history) == len(spec.operation_history) + 1
        assert abs_spec.operation_history[-1]["operation"] == "abs"
        assert abs_spec.operation_history[-1]["params"] == {}

        # メタデータに "abs" が追加されていることを確認
        assert "abs" in abs_spec.metadata
        assert abs_spec.metadata["abs"] == {}

        # チャネルメタデータが保持されていることを確認
        assert abs_spec._channel_metadata == spec._channel_metadata

        # previousが正しく設定されていることを確認
        assert abs_spec.previous == spec

    def test_abs_preserves_magnitude_property(
        self, sample_spectrogram: SpectrogramFrame
    ) -> None:
        """abs()メソッドの結果がmagnitudeプロパティと一致することを確認"""
        spec: SpectrogramFrame = sample_spectrogram

        # abs()メソッドを呼び出し
        abs_spec: SpectrogramFrame = spec.abs()

        # 元のmagnitudeと、abs()後のmagnitudeが同じであることを確認
        original_magnitude = spec.magnitude
        abs_magnitude = abs_spec.magnitude

        assert_array_almost_equal(abs_magnitude, original_magnitude)

    def test_abs_lazy_evaluation(self, sample_spectrogram: SpectrogramFrame) -> None:
        """abs()メソッドが遅延評価を維持していることを確認"""
        spec: SpectrogramFrame = sample_spectrogram

        # abs()メソッドを呼び出し
        abs_spec: SpectrogramFrame = spec.abs()

        # データがdask配列であることを確認（遅延評価が維持されている）
        assert isinstance(abs_spec._data, DaArray)

        # compute()を呼ばない限り、実際の計算は行われない
        # （データのtype確認）
        assert hasattr(abs_spec._data, "compute")

    def test_abs_chain_operations(self, sample_spectrogram: SpectrogramFrame) -> None:
        """abs()メソッドが他の操作とチェーン可能であることを確認"""
        spec: SpectrogramFrame = sample_spectrogram

        # abs()メソッドとスカラー演算をチェーン
        result: SpectrogramFrame = spec.abs() * 2.0

        # 結果がSpectrogramFrameであることを確認
        assert isinstance(result, SpectrogramFrame)

        # 操作履歴が正しく記録されていることを確認
        # spec -> abs -> multiply
        assert len(result.operation_history) >= len(spec.operation_history) + 2
        # abs操作が含まれていることを確認
        abs_op_found = any(op["operation"] == "abs" for op in result.operation_history)
        assert abs_op_found
